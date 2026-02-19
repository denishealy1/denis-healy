import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', _('Admin')
    PARTNER = 'PARTNER', _('Partner')
    STUDENT = 'STUDENT', _('Student')


class ProfileStatus(models.TextChoices):
    INVITED = 'INVITED', _('Invited')
    ONBOARDING = 'ONBOARDING', _('Onboarding')
    ONBOARDED = 'ONBOARDED', _('Onboarded')


class PlacementStatus(models.TextChoices):
    PROPOSED = 'PROPOSED', _('Proposed')
    CONFIRMED = 'CONFIRMED', _('Confirmed')
    ACTIVE = 'ACTIVE', _('Active')
    COMPLETED = 'COMPLETED', _('Completed')


class AccommodationType(models.TextChoices):
    RESIDENCE = 'RESIDENCE', _('Residence')
    APARTMENT = 'APARTMENT', _('Apartment')


class TransferType(models.TextChoices):
    PICKUP = 'PICKUP', _('Pickup')
    DROPOFF = 'DROPOFF', _('Dropoff')


class DocumentType(models.TextChoices):
    CERTIFICATE = 'CERTIFICATE', _('Certificate')


class PortalUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.ADMIN)
        return self._create_user(email, password, **extra_fields)


class PartnerOrg(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=120, blank=True)
    contact_email = models.EmailField(blank=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.STUDENT)
    partner_org = models.ForeignKey(PartnerOrg, null=True, blank=True, on_delete=models.SET_NULL)
    preferred_language = models.CharField(max_length=2, choices=settings.LANGUAGES, default='en')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = PortalUserManager()

    def __str__(self):
        return self.email


def validate_file_size(file_obj):
    if file_obj.size > 5 * 1024 * 1024:
        raise ValidationError(_('File too large (max 5MB).'))


class Project(models.Model):
    partner_org = models.ForeignKey(PartnerOrg, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    project_ref = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    destination_city = models.CharField(max_length=120, default='Malaga')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.project_ref} - {self.name}'


class StudentInvite(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='invites')
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'email')

    @classmethod
    def build(cls, project, email, created_by):
        return cls(
            project=project,
            email=email,
            token=secrets.token_urlsafe(32),
            expires_at=timezone.now() + timedelta(days=14),
            created_by=created_by,
        )


class StudentProfile(models.Model):
    LANGUAGE_LEVELS = [(lvl, lvl) for lvl in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']]
    SECTOR_CHOICES = [
        ('tourism', _('Tourism')),
        ('it', _('IT')),
        ('education', _('Education')),
        ('health', _('Health')),
        ('business', _('Business')),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='students')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    nationality = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    language_level = models.CharField(max_length=2, choices=LANGUAGE_LEVELS, default='A1')
    sector_preferences = models.JSONField(default=list, blank=True)
    skills = models.TextField(blank=True)
    cv_file = models.FileField(upload_to='cv/', blank=True, validators=[FileExtensionValidator(['pdf']), validate_file_size])
    id_file = models.FileField(upload_to='id/', blank=True, validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png']), validate_file_size])
    flight_number = models.CharField(max_length=50, blank=True)
    arrival_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ProfileStatus.choices, default=ProfileStatus.ONBOARDING)

    @property
    def checklist(self):
        return {
            'personal': bool(self.first_name and self.last_name),
            'documents': bool(self.cv_file and self.id_file),
            'preferences': bool(self.language_level and self.sector_preferences),
        }


class Company(models.Model):
    name = models.CharField(max_length=255)
    sector = models.CharField(max_length=120)
    address = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=120)
    contact_email = models.EmailField()
    capacity = models.IntegerField(default=1)
    verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)


class Placement(models.Model):
    student_profile = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='placement')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    role_title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    supervisor_name = models.CharField(max_length=120)
    supervisor_email = models.EmailField()
    status = models.CharField(max_length=20, choices=PlacementStatus.choices, default=PlacementStatus.PROPOSED)


class AccommodationUnit(models.Model):
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=20, choices=AccommodationType.choices)
    address = models.CharField(max_length=255)
    notes = models.TextField(blank=True)


class Booking(models.Model):
    student_profile = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='booking')
    unit = models.ForeignKey(AccommodationUnit, on_delete=models.CASCADE)
    check_in = models.DateField()
    check_out = models.DateField()
    room_label = models.CharField(max_length=50, blank=True)


class Transfer(models.Model):
    student_profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='transfers')
    type = models.CharField(max_length=20, choices=TransferType.choices)
    datetime = models.DateTimeField()
    flight_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)


class GeneratedDocument(models.Model):
    student_profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=20, choices=DocumentType.choices)
    file = models.FileField(upload_to='generated/')
    created_at = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)


class AuditLog(models.Model):
    actor_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=120)
    entity_type = models.CharField(max_length=120)
    entity_id = models.CharField(max_length=64)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)


def log_action(actor, action, entity, details=None, ip=None):
    AuditLog.objects.create(
        actor_user=actor,
        action=action,
        entity_type=entity.__class__.__name__,
        entity_id=str(entity.pk),
        details=details or {},
        ip=ip,
    )
