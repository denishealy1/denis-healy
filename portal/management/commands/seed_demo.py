from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from portal.models import PartnerOrg, Project, StudentInvite, StudentProfile, User


class Command(BaseCommand):
    help = 'Seed demo data'

    def handle(self, *args, **options):
        org, _ = PartnerOrg.objects.get_or_create(name='Demo Partner', defaults={'country': 'ES'})
        admin, _ = User.objects.get_or_create(email='admin@example.com', defaults={'role': User.Role.ADMIN, 'is_staff': True, 'is_superuser': True})
        admin.set_password('AdminPass123!')
        admin.save()

        partner, _ = User.objects.get_or_create(email='partner@example.com', defaults={'role': User.Role.PARTNER, 'partner_org': org})
        partner.partner_org = org
        partner.set_password('PartnerPass123!')
        partner.save()

        project, _ = Project.objects.get_or_create(
            partner_org=org,
            project_ref='MAL-2026-001',
            defaults={'name': 'Demo Malaga Mobility', 'start_date': timezone.now().date(), 'end_date': timezone.now().date() + timedelta(days=90), 'destination_city': 'Malaga'},
        )

        student, _ = User.objects.get_or_create(email='student@example.com', defaults={'role': User.Role.STUDENT})
        student.set_password('StudentPass123!')
        student.save()

        StudentProfile.objects.get_or_create(user=student, defaults={
            'project': project, 'first_name': 'Demo', 'last_name': 'Student', 'status': StudentProfile.Status.ONBOARDING,
        })
        StudentInvite.objects.get_or_create(project=project, email='student@example.com', defaults={
            'expires_at': timezone.now() + timedelta(days=14), 'created_by': partner,
        })
        self.stdout.write(self.style.SUCCESS('Seeded demo users and project'))
