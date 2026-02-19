from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import PartnerOrg, Project, StudentProfile, User, UserRole


class Command(BaseCommand):
    help = 'Seed demo data'

    def handle(self, *args, **options):
        org, _ = PartnerOrg.objects.get_or_create(name='Demo Partner', defaults={'country': 'ES'})
        admin, _ = User.objects.get_or_create(email='admin@example.com', defaults={'role': UserRole.ADMIN, 'is_staff': True, 'is_superuser': True})
        admin.set_password('AdminPass123!')
        admin.save()
        partner, _ = User.objects.get_or_create(email='partner@example.com', defaults={'role': UserRole.PARTNER, 'partner_org': org})
        partner.set_password('PartnerPass123!')
        partner.save()
        student, _ = User.objects.get_or_create(email='student@example.com', defaults={'role': UserRole.STUDENT})
        student.set_password('StudentPass123!')
        student.save()
        project, _ = Project.objects.get_or_create(
            partner_org=org,
            project_ref='MAL-001',
            defaults={'name': 'Demo Mobility', 'start_date': timezone.now().date(), 'end_date': timezone.now().date()},
        )
        StudentProfile.objects.get_or_create(user=student, project=project, defaults={'first_name': 'Demo', 'last_name': 'Student'})
        self.stdout.write(self.style.SUCCESS('Seed complete'))
