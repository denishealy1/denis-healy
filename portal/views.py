from datetime import timedelta
from io import BytesIO
import logging
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.translation import gettext as _
from reportlab.pdfgen import canvas

from .decorators import role_required
from .forms import (
    BookingForm,
    CompanyForm,
    CSVInviteUploadForm,
    InviteForm,
    LoginForm,
    PlacementForm,
    ProjectForm,
    StudentProfileForm,
    StudentSignupForm,
    TransferForm,
)
from .models import (
    AccommodationUnit,
    Booking,
    Company,
    GeneratedDocument,
    Placement,
    Project,
    StudentInvite,
    StudentProfile,
    Transfer,
    User,
)
from .utils import log_action

logger = logging.getLogger(__name__)


class UserLoginView(LoginView):
    template_name = 'auth/login.html'
    authentication_form = LoginForm


class UserLogoutView(LogoutView):
    pass


def set_language_preference(request):
    lang = request.POST.get('language', 'en')
    translation.activate(lang)
    request.session[translation.LANGUAGE_SESSION_KEY] = lang
    if request.user.is_authenticated:
        request.user.preferred_language = lang
        request.user.save(update_fields=['preferred_language'])
    return redirect(request.META.get('HTTP_REFERER', reverse('dashboard')))


@login_required
def dashboard(request):
    user = request.user
    if user.role == User.Role.ADMIN:
        projects = Project.objects.annotate(
            invited=Count('studentinvite', distinct=True),
            onboarded=Count('studentprofile', filter=Q(studentprofile__status=StudentProfile.Status.ONBOARDED), distinct=True),
            placed=Count('studentprofile__placement', distinct=True),
            completed=Count('studentprofile__placement', filter=Q(studentprofile__placement__status=Placement.Status.COMPLETED), distinct=True),
        )
        return render(request, 'portal/admin_dashboard.html', {'projects': projects})
    if user.role == User.Role.PARTNER:
        projects = Project.objects.filter(partner_org=user.partner_org)
        return render(request, 'portal/partner_dashboard.html', {'projects': projects})
    profile = get_object_or_404(StudentProfile, user=user)
    return render(request, 'portal/student_dashboard.html', {'profile': profile})


@login_required
@role_required(User.Role.PARTNER)
def project_create(request):
    form = ProjectForm(request.POST or None)
    if form.is_valid():
        project = form.save(commit=False)
        project.partner_org = request.user.partner_org
        project.save()
        log_action('project_created', project, actor=request.user, request=request)
        messages.success(request, _('Project created successfully'))
        return redirect('partner_project_detail', project_id=project.id)
    return render(request, 'portal/project_form.html', {'form': form})


def _project_for_partner_or_admin(user, project_id):
    qs = Project.objects.all() if user.role == User.Role.ADMIN else Project.objects.filter(partner_org=user.partner_org)
    return get_object_or_404(qs, id=project_id)


@login_required
def partner_project_detail(request, project_id):
    if request.user.role not in [User.Role.PARTNER, User.Role.ADMIN]:
        raise PermissionDenied
    project = _project_for_partner_or_admin(request.user, project_id)
    invites = StudentInvite.objects.filter(project=project)
    students = StudentProfile.objects.filter(project=project)
    return render(request, 'portal/project_detail.html', {'project': project, 'invites': invites, 'students': students})


@login_required
@role_required(User.Role.PARTNER)
def invite_students(request, project_id):
    project = get_object_or_404(Project, id=project_id, partner_org=request.user.partner_org)
    form = InviteForm(request.POST or None)
    links = []
    if form.is_valid():
        for email in form.cleaned_data['emails']:
            invite, created = StudentInvite.objects.get_or_create(
                project=project,
                email=email,
                defaults={
                    'expires_at': timezone.now() + timedelta(days=14),
                    'created_by': request.user,
                },
            )
            link = request.build_absolute_uri(reverse('invite_signup', kwargs={'token': invite.token}))
            links.append((email, link, created))
            logger.info('Invite generated for %s: %s', email, link)
            log_action('invite_created', invite, actor=request.user, details={'email': email}, request=request)
        messages.success(request, _('Invites generated'))
    return render(request, 'portal/invite_form.html', {'project': project, 'form': form, 'links': links})


@login_required
@role_required(User.Role.PARTNER)
def invite_csv_upload(request, project_id):
    project = get_object_or_404(Project, id=project_id, partner_org=request.user.partner_org)
    form = CSVInviteUploadForm(request.POST or None, request.FILES or None)
    report = None
    if form.is_valid():
        created, duplicate = [], []
        for row in form.parse_rows():
            email = (row.get('email') or '').strip().lower()
            if not email:
                continue
            invite, was_created = StudentInvite.objects.get_or_create(
                project=project,
                email=email,
                defaults={'expires_at': timezone.now() + timedelta(days=14), 'created_by': request.user},
            )
            if was_created:
                created.append(email)
            else:
                duplicate.append(email)
        report = {'created': created, 'duplicate': duplicate}
        messages.success(request, _('CSV processed'))
    return render(request, 'portal/invite_csv.html', {'form': form, 'project': project, 'report': report})


def invite_signup(request, token):
    invite = get_object_or_404(StudentInvite, token=token)
    if not invite.is_valid:
        messages.error(request, _('Invite is invalid or expired'))
        return redirect('login')

    form = StudentSignupForm(request.POST or None, initial={'email': invite.email})
    if form.is_valid():
        user = User.objects.create_user(
            email=invite.email,
            password=form.cleaned_data['password'],
            role=User.Role.STUDENT,
            preferred_language=request.LANGUAGE_CODE,
        )
        StudentProfile.objects.create(
            user=user,
            project=invite.project,
            first_name='',
            last_name='',
            status=StudentProfile.Status.ONBOARDING,
        )
        invite.used_at = timezone.now()
        invite.save(update_fields=['used_at'])
        login(request, user)
        return redirect('student_onboarding')
    return render(request, 'portal/invite_signup.html', {'invite': invite, 'form': form})


@login_required
@role_required(User.Role.STUDENT)
def student_onboarding(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    form = StudentProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if form.is_valid():
        profile = form.save(commit=False)
        required_done = bool(profile.first_name and profile.last_name and profile.cv_file and profile.id_file)
        profile.status = StudentProfile.Status.ONBOARDED if required_done else StudentProfile.Status.ONBOARDING
        profile.save()
        if required_done:
            log_action('profile_submitted', profile, actor=request.user, request=request)
            messages.success(request, _('Profile completed'))
        else:
            messages.warning(request, _('Profile saved but checklist is incomplete'))
        return redirect('student_onboarding')

    checklist = {
        'name': bool(profile.first_name and profile.last_name),
        'cv': bool(profile.cv_file),
        'id': bool(profile.id_file),
    }
    return render(request, 'portal/student_onboarding.html', {'form': form, 'profile': profile, 'checklist': checklist})


@login_required
def student_detail(request, profile_id):
    if request.user.role != User.Role.ADMIN:
        raise PermissionDenied
    profile = get_object_or_404(StudentProfile, id=profile_id)
    placement = getattr(profile, 'placement', None)
    booking = getattr(profile, 'booking', None)
    transfers = Transfer.objects.filter(student_profile=profile)

    pform = PlacementForm(request.POST or None, instance=placement, prefix='p')
    bform = BookingForm(request.POST or None, instance=booking, prefix='b')
    tform = TransferForm(request.POST or None, prefix='t')

    if request.method == 'POST':
        if 'save_placement' in request.POST and pform.is_valid():
            p = pform.save(commit=False)
            p.student_profile = profile
            p.save()
            log_action('placement_assigned', p, actor=request.user, request=request)
            messages.success(request, _('Placement saved'))
            return redirect('student_detail', profile_id=profile.id)
        if 'save_booking' in request.POST and bform.is_valid():
            b = bform.save(commit=False)
            b.student_profile = profile
            b.save()
            log_action('booking_updated', b, actor=request.user, request=request)
            messages.success(request, _('Booking saved'))
            return redirect('student_detail', profile_id=profile.id)
        if 'save_transfer' in request.POST and tform.is_valid():
            t = tform.save(commit=False)
            t.student_profile = profile
            t.save()
            log_action('transfer_updated', t, actor=request.user, request=request)
            messages.success(request, _('Transfer saved'))
            return redirect('student_detail', profile_id=profile.id)

    docs = GeneratedDocument.objects.filter(student_profile=profile)
    return render(request, 'portal/student_detail.html', {
        'profile': profile, 'placement': placement, 'booking': booking, 'transfers': transfers,
        'pform': pform, 'bform': bform, 'tform': tform, 'docs': docs,
    })


@login_required
@role_required(User.Role.ADMIN)
def companies(request):
    form = CompanyForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, _('Company saved'))
        return redirect('companies')
    return render(request, 'portal/companies.html', {'form': form, 'companies': Company.objects.all()})


@login_required
@role_required(User.Role.ADMIN)
def generate_certificate(request, profile_id):
    profile = get_object_or_404(StudentProfile, id=profile_id)
    placement = getattr(profile, 'placement', None)
    if not placement or placement.status not in [Placement.Status.CONFIRMED, Placement.Status.COMPLETED]:
        messages.error(request, _('Placement must be confirmed/completed'))
        return redirect('student_detail', profile_id=profile.id)

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 800, 'European Era Mobility Certificate')
    p.drawString(100, 780, f'Student: {profile.first_name} {profile.last_name}')
    p.drawString(100, 760, f'Project ref: {profile.project.project_ref}')
    p.drawString(100, 740, f'Company: {placement.company.name}')
    p.drawString(100, 720, f'Dates: {placement.start_date} to {placement.end_date}')
    p.drawString(100, 700, f'Generated: {timezone.now().date()}')
    p.save()

    filename = f'certificate_{profile.id}_{timezone.now().strftime("%Y%m%d%H%M%S")}.pdf'
    doc = GeneratedDocument.objects.create(
        student_profile=profile,
        doc_type=GeneratedDocument.DocType.CERTIFICATE,
    )
    doc.file.save(filename, ContentFile(buffer.getvalue()))
    log_action('certificate_generated', doc, actor=request.user, request=request)
    messages.success(request, _('Certificate generated'))
    return redirect('student_detail', profile_id=profile.id)


@login_required
@role_required(User.Role.STUDENT)
def student_logistics(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    return render(request, 'portal/student_logistics.html', {
        'booking': getattr(profile, 'booking', None),
        'transfers': Transfer.objects.filter(student_profile=profile),
        'documents': GeneratedDocument.objects.filter(student_profile=profile),
    })


def custom_403(request, exception=None):
    return render(request, '403.html', status=403)
