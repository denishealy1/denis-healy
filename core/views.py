from datetime import timedelta
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .forms import (
    BookingForm,
    CompanyForm,
    InviteAcceptForm,
    InviteCSVForm,
    InviteForm,
    PlacementForm,
    ProjectForm,
    StudentProfileForm,
    TransferForm,
)
from .models import (
    Booking,
    Company,
    GeneratedDocument,
    Placement,
    PlacementStatus,
    ProfileStatus,
    Project,
    StudentInvite,
    StudentProfile,
    Transfer,
    UserRole,
    log_action,
)


def role_required(*roles):
    def decorator(view):
        def wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                return render(request, 'core/403.html', status=403)
            return view(request, *args, **kwargs)
        return login_required(wrapped)
    return decorator


@login_required
def dashboard(request):
    if request.user.role == UserRole.ADMIN:
        return redirect('admin_dashboard')
    if request.user.role == UserRole.PARTNER:
        return redirect('partner_dashboard')
    return redirect('student_dashboard')


@role_required(UserRole.PARTNER)
def partner_dashboard(request):
    projects = Project.objects.filter(partner_org=request.user.partner_org).order_by('-created_at')
    return render(request, 'core/partner_dashboard.html', {'projects': projects})


@role_required(UserRole.PARTNER)
def project_create(request):
    form = ProjectForm(request.POST or None)
    if form.is_valid():
        project = form.save(commit=False)
        project.partner_org = request.user.partner_org
        project.save()
        log_action(request.user, 'project_created', project, ip=request.META.get('REMOTE_ADDR'))
        messages.success(request, _('Project created'))
        return redirect('partner_dashboard')
    return render(request, 'core/project_form.html', {'form': form})


@role_required(UserRole.PARTNER)
def invite_students(request, project_id):
    project = get_object_or_404(Project, pk=project_id, partner_org=request.user.partner_org)
    form = InviteForm(request.POST or None)
    csv_form = InviteCSVForm(request.POST or None, request.FILES or None)
    links = []
    report = None
    if request.method == 'POST' and 'emails' in request.POST and form.is_valid():
        for email in form.cleaned_data['emails']:
            invite, created = StudentInvite.objects.get_or_create(
                project=project,
                email=email,
                defaults={
                    'token': StudentInvite.build(project, email, request.user).token,
                    'expires_at': timezone.now() + timedelta(days=14),
                    'created_by': request.user,
                },
            )
            if created:
                log_action(request.user, 'invite_created', invite, {'email': email})
                print(f'Invite created for {email}: {request.build_absolute_uri(reverse("invite_accept", args=[invite.token]))}')
            links.append(request.build_absolute_uri(reverse('invite_accept', args=[invite.token])))
    if request.method == 'POST' and 'csv_file' in request.FILES and csv_form.is_valid():
        rows = csv_form.parse()
        created = 0
        skipped = 0
        for row in rows:
            email = row['email'].strip()
            _, was_created = StudentInvite.objects.get_or_create(
                project=project,
                email=email,
                defaults={
                    'token': StudentInvite.build(project, email, request.user).token,
                    'expires_at': timezone.now() + timedelta(days=14),
                    'created_by': request.user,
                },
            )
            created += int(was_created)
            skipped += int(not was_created)
        report = {'created': created, 'skipped': skipped}
    return render(request, 'core/invite_students.html', {
        'project': project,
        'form': form,
        'csv_form': csv_form,
        'links': links,
        'report': report,
    })


def invite_accept(request, token):
    invite = get_object_or_404(StudentInvite, token=token)
    if invite.used_at or invite.expires_at < timezone.now():
        messages.error(request, _('Invite is invalid or expired'))
        return redirect('login')
    form = InviteAcceptForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        if form.cleaned_data['email'].lower() != invite.email.lower():
            form.add_error('email', _('Must match invite email'))
        else:
            user.role = UserRole.STUDENT
            user.preferred_language = 'en'
            user.save()
            StudentProfile.objects.create(
                user=user,
                project=invite.project,
                first_name='',
                last_name='',
                status=ProfileStatus.ONBOARDING,
            )
            invite.used_at = timezone.now()
            invite.save(update_fields=['used_at'])
            login(request, user)
            messages.success(request, _('Account created. Complete your profile.'))
            return redirect('student_profile')
    return render(request, 'core/invite_accept.html', {'form': form, 'invite': invite})


@role_required(UserRole.STUDENT)
def student_dashboard(request):
    profile = request.user.student_profile
    return render(request, 'core/student_dashboard.html', {'profile': profile})


@role_required(UserRole.STUDENT)
def student_profile(request):
    profile = request.user.student_profile
    form = StudentProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if form.is_valid():
        profile = form.save(commit=False)
        if all(profile.checklist.values()):
            profile.status = ProfileStatus.ONBOARDED
        profile.save()
        log_action(request.user, 'profile_submitted', profile)
        messages.success(request, _('Profile updated'))
        return redirect('student_dashboard')
    return render(request, 'core/student_profile.html', {'form': form, 'profile': profile})


@role_required(UserRole.ADMIN)
def admin_dashboard(request):
    projects = Project.objects.annotate(
        invited=Count('invites'),
        onboarded=Count('students', filter=Q(students__status=ProfileStatus.ONBOARDED)),
        placed=Count('students__placement', filter=Q(students__placement__status__in=[PlacementStatus.CONFIRMED, PlacementStatus.ACTIVE])),
        completed=Count('students__placement', filter=Q(students__placement__status=PlacementStatus.COMPLETED)),
    )
    return render(request, 'core/admin_dashboard.html', {'projects': projects})


@role_required(UserRole.ADMIN)
def project_detail(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    return render(request, 'core/project_detail.html', {'project': project})


@role_required(UserRole.ADMIN)
def company_list(request):
    companies = Company.objects.all()
    return render(request, 'core/company_list.html', {'companies': companies})


@role_required(UserRole.ADMIN)
def company_edit(request, pk=None):
    company = Company.objects.filter(pk=pk).first()
    form = CompanyForm(request.POST or None, instance=company)
    if form.is_valid():
        form.save()
        return redirect('company_list')
    return render(request, 'core/company_form.html', {'form': form})


@role_required(UserRole.ADMIN)
def student_admin_detail(request, pk):
    student = get_object_or_404(StudentProfile, pk=pk)
    placement = Placement.objects.filter(student_profile=student).first()
    booking = Booking.objects.filter(student_profile=student).first()
    placement_form = PlacementForm(request.POST or None, instance=placement, prefix='pl')
    booking_form = BookingForm(request.POST or None, instance=booking, prefix='bk')
    transfer_form = TransferForm(request.POST or None, prefix='tr')

    if request.method == 'POST':
        if 'save_placement' in request.POST and placement_form.is_valid():
            obj = placement_form.save(commit=False)
            obj.student_profile = student
            obj.save()
            log_action(request.user, 'placement_assigned', obj)
            messages.success(request, _('Placement saved'))
            return redirect('student_admin_detail', pk=student.pk)
        if 'save_booking' in request.POST and booking_form.is_valid():
            obj = booking_form.save(commit=False)
            obj.student_profile = student
            obj.save()
            log_action(request.user, 'booking_changed', obj)
            return redirect('student_admin_detail', pk=student.pk)
        if 'save_transfer' in request.POST and transfer_form.is_valid():
            obj = transfer_form.save(commit=False)
            obj.student_profile = student
            obj.save()
            log_action(request.user, 'transfer_changed', obj)
            return redirect('student_admin_detail', pk=student.pk)

    return render(request, 'core/student_admin_detail.html', {
        'student': student,
        'placement_form': placement_form,
        'booking_form': booking_form,
        'transfer_form': transfer_form,
        'transfers': student.transfers.all(),
    })


@role_required(UserRole.ADMIN)
def generate_certificate(request, pk):
    student = get_object_or_404(StudentProfile, pk=pk)
    placement = getattr(student, 'placement', None)
    if not placement or placement.status not in [PlacementStatus.CONFIRMED, PlacementStatus.COMPLETED]:
        messages.error(request, _('Placement must be confirmed/completed'))
        return redirect('student_admin_detail', pk=pk)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.drawString(100, 800, 'European Era Mobility Certificate')
    pdf.drawString(100, 770, f'Student: {student.first_name} {student.last_name}')
    pdf.drawString(100, 750, f'Project Ref: {student.project.project_ref}')
    pdf.drawString(100, 730, f'Company: {placement.company.name}')
    pdf.drawString(100, 710, f'Dates: {placement.start_date} - {placement.end_date}')
    pdf.drawString(100, 690, f'Generated: {timezone.now().date()}')
    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    filename = f'certificate_{student.id}_{timezone.now().strftime("%Y%m%d%H%M%S")}.pdf'
    doc = GeneratedDocument.objects.create(student_profile=student, doc_type='CERTIFICATE', meta={'placement': placement.id})
    doc.file.save(filename, buffer)
    log_action(request.user, 'certificate_generated', doc)
    return FileResponse(doc.file.open('rb'), as_attachment=True, filename=filename)


@role_required(UserRole.STUDENT)
def student_logistics(request):
    profile = request.user.student_profile
    return render(request, 'core/student_logistics.html', {'profile': profile})


def custom_403(request, exception=None):
    return render(request, 'core/403.html', status=403)
