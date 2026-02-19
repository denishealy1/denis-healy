import pytest
from django.urls import reverse
from django.utils import timezone

from core.models import PartnerOrg, Project, StudentProfile, User, UserRole


@pytest.fixture
def setup_data(db):
    org1 = PartnerOrg.objects.create(name='Org1')
    org2 = PartnerOrg.objects.create(name='Org2')
    partner1 = User.objects.create_user(email='p1@example.com', password='x', role=UserRole.PARTNER, partner_org=org1)
    partner2 = User.objects.create_user(email='p2@example.com', password='x', role=UserRole.PARTNER, partner_org=org2)
    admin = User.objects.create_user(email='a@example.com', password='x', role=UserRole.ADMIN, is_staff=True)
    student = User.objects.create_user(email='s@example.com', password='x', role=UserRole.STUDENT)
    p1 = Project.objects.create(partner_org=org1, name='P1', project_ref='1', start_date=timezone.now(), end_date=timezone.now())
    p2 = Project.objects.create(partner_org=org2, name='P2', project_ref='2', start_date=timezone.now(), end_date=timezone.now())
    StudentProfile.objects.create(user=student, project=p1, first_name='S', last_name='T')
    return partner1, partner2, admin, student, p1, p2


def test_partner_cannot_access_other_org_project(client, setup_data):
    partner1, _, _, _, _, p2 = setup_data
    client.login(email=partner1.email, password='x')
    resp = client.get(reverse('invite_students', args=[p2.id]))
    assert resp.status_code == 404


def test_student_cannot_access_admin(client, setup_data):
    _, _, _, student, _, _ = setup_data
    client.login(email=student.email, password='x')
    resp = client.get(reverse('admin_dashboard'))
    assert resp.status_code == 403
