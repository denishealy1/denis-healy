import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from portal.models import Company, PartnerOrg, Placement, Project, StudentInvite, StudentProfile, User


@pytest.mark.django_db
def test_end_to_end_smoke_flow(client):
    org = PartnerOrg.objects.create(name='Org')
    admin = User.objects.create_user(email='admin@e.com', password='x', role=User.Role.ADMIN)
    partner = User.objects.create_user(email='partner@e.com', password='x', role=User.Role.PARTNER, partner_org=org)

    client.login(username='partner@e.com', password='x')
    client.post(reverse('project_create'), {
        'name': 'Project', 'project_ref': 'REF', 'start_date': '2026-01-01', 'end_date': '2026-02-01',
        'destination_city': 'Malaga', 'notes': 'n'
    })
    project = Project.objects.get(project_ref='REF')

    client.post(reverse('invite_students', kwargs={'project_id': project.id}), {'emails': 'student@e.com'})
    invite = StudentInvite.objects.get(email='student@e.com')

    client.logout()
    client.post(reverse('invite_signup', kwargs={'token': invite.token}), {'password': 'Password123!'})
    student = User.objects.get(email='student@e.com')
    profile = StudentProfile.objects.get(user=student)
    profile.first_name='A'; profile.last_name='B'; profile.status=StudentProfile.Status.ONBOARDED; profile.save()

    company = Company.objects.create(name='C', sector='IT', address='A', contact_name='CN', contact_email='c@c.com', capacity=2)
    placement = Placement.objects.create(student_profile=profile, company=company, role_title='Intern', start_date='2026-01-02', end_date='2026-01-30', supervisor_name='Sup', supervisor_email='sup@c.com', status=Placement.Status.CONFIRMED)

    client.logout(); client.login(username='admin@e.com', password='x')
    resp = client.get(reverse('generate_certificate', kwargs={'profile_id': profile.id}))
    assert resp.status_code == 302
