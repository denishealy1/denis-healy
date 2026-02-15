import pytest
from django.urls import reverse
from portal.models import PartnerOrg, Project, StudentProfile, User


@pytest.mark.django_db
def test_partner_cannot_see_other_org_project(client):
    org1 = PartnerOrg.objects.create(name='Org1')
    org2 = PartnerOrg.objects.create(name='Org2')
    partner = User.objects.create_user(email='p1@example.com', password='x', role=User.Role.PARTNER, partner_org=org1)
    project = Project.objects.create(partner_org=org2, name='P', project_ref='R', start_date='2026-01-01', end_date='2026-02-01')
    client.login(username='p1@example.com', password='x')
    resp = client.get(reverse('partner_project_detail', kwargs={'project_id': project.id}))
    assert resp.status_code == 404


@pytest.mark.django_db
def test_student_cannot_access_admin_pages(client):
    student = User.objects.create_user(email='s@example.com', password='x', role=User.Role.STUDENT)
    client.login(username='s@example.com', password='x')
    resp = client.get(reverse('companies'))
    assert resp.status_code == 403
