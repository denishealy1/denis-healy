import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from core.models import Company, PartnerOrg, PlacementStatus, Project, StudentInvite, StudentProfile, User, UserRole


@pytest.mark.django_db
def test_smoke_flow(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    org = PartnerOrg.objects.create(name='Org')
    partner = User.objects.create_user(email='partner@test.com', password='pass', role=UserRole.PARTNER, partner_org=org)
    admin = User.objects.create_user(email='admin@test.com', password='pass', role=UserRole.ADMIN, is_staff=True)

    client.login(email=partner.email, password='pass')
    client.post(reverse('project_create'), {
        'name': 'Proj', 'project_ref': 'R1', 'start_date': '2025-01-01', 'end_date': '2025-02-01', 'destination_city': 'Malaga', 'notes': ''
    })
    project = Project.objects.get(project_ref='R1')
    client.post(reverse('invite_students', args=[project.id]), {'emails': 'student@flow.com'})
    invite = StudentInvite.objects.get(email='student@flow.com')

    client.logout()
    client.post(reverse('invite_accept', args=[invite.token]), {
        'email': 'student@flow.com', 'password1': 'StrongPass123!!', 'password2': 'StrongPass123!!'
    })
    student = User.objects.get(email='student@flow.com')
    cv = SimpleUploadedFile('cv.pdf', b'pdf', content_type='application/pdf')
    idf = SimpleUploadedFile('id.pdf', b'pdf', content_type='application/pdf')
    client.post(reverse('student_profile'), {
        'first_name': 'Stu', 'last_name': 'Dent', 'language_level': 'B1', 'sector_preferences': ['it'], 'skills': 'python',
        'cv_file': cv, 'id_file': idf
    }, follow=True)

    profile = StudentProfile.objects.get(user=student)
    company = Company.objects.create(name='Comp', sector='IT', address='Addr', contact_name='N', contact_email='c@x.com', capacity=2)
    client.logout()
    client.login(email=admin.email, password='pass')
    client.post(reverse('student_admin_detail', args=[profile.id]), {
        'pl-company': company.id, 'pl-role_title': 'Intern', 'pl-start_date': '2025-01-02', 'pl-end_date': '2025-01-30',
        'pl-supervisor_name': 'Sup', 'pl-supervisor_email': 'sup@x.com', 'pl-status': PlacementStatus.CONFIRMED, 'save_placement': '1'
    })
    cert_resp = client.get(reverse('generate_certificate', args=[profile.id]))
    assert cert_resp.status_code == 200
