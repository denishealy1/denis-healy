from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email required')
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
        extra_fields.setdefault('role', User.Role.ADMIN)
        return self._create_user(email, password, **extra_fields)


class PartnerOrg(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        PARTNER = 'PARTNER', _('Partner')
        STUDENT = 'STUDENT', _('Student')

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    partner_org = models.ForeignKey(PartnerOrg, null=True, blank=True, on_delete=models.SET_NULL)
    preferred_language = models.CharField(max_length=2, choices=settings.LANGUAGES, default='en')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()


class Project(models.Model):
    partner_org = models.ForeignKey(PartnerOrg, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    project_ref = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    destination_city = models.CharField(max_length=100, default='Malaga')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class StudentInvite(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'email')

    @property
    def is_valid(self):
        return self.used_at is None and self.expires_at > timezone.now()


class StudentProfile(models.Model):
    class Status(models.TextChoices):
        INVITED = 'INVITED', _('Invited')
        ONBOARDING = 'ONBOARDING', _('Onboarding')
        ONBOARDED = 'ONBOARDED', _('Onboarded')

    class Level(models.TextChoices):
        A1 = 'A1', 'A1'
        A2 = 'A2', 'A2'
        B1 = 'B1', 'B1'
        B2 = 'B2', 'B2'
        C1 = 'C1', 'C1'
        C2 = 'C2', 'C2'

    SECTOR_CHOICES = [
        ('tourism', _('Tourism')),
        ('it', _('IT')),
        ('health', _('Health')),
        ('education', _('Education')),
        ('engineering', _('Engineering')),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    language_level = models.CharField(max_length=2, choices=Level.choices, default=Level.B1)
    sector_preferences = models.JSONField(default=list, blank=True)
    skills = models.TextField(blank=True)
    cv_file = models.FileField(upload_to='cv/', blank=True, validators=[FileExtensionValidator(['pdf'])])
    id_file = models.FileField(upload_to='id/', blank=True, validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])])
    flight_number = models.CharField(max_length=50, blank=True)
    arrival_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INVITED)


class Company(models.Model):
    name = models.CharField(max_length=255)
    sector = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    capacity = models.PositiveIntegerField(default=1)
    verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)


class Placement(models.Model):
    class Status(models.TextChoices):
        PROPOSED = 'PROPOSED', _('Proposed')
        CONFIRMED = 'CONFIRMED', _('Confirmed')
        ACTIVE = 'ACTIVE', _('Active')
        COMPLETED = 'COMPLETED', _('Completed')

    student_profile = models.OneToOneField(StudentProfile, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    role_title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    supervisor_name = models.CharField(max_length=255)
    supervisor_email = models.EmailField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROPOSED)


class AccommodationUnit(models.Model):
    class Type(models.TextChoices):
        RESIDENCE = 'RESIDENCE', _('Residence')
        APARTMENT = 'APARTMENT', _('Apartment')

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=Type.choices)
    address = models.CharField(max_length=255)
    notes = models.TextField(blank=True)


class Booking(models.Model):
    student_profile = models.OneToOneField(StudentProfile, on_delete=models.CASCADE)
    unit = models.ForeignKey(AccommodationUnit, on_delete=models.PROTECT)
    check_in = models.DateField()
    check_out = models.DateField()
    room_label = models.CharField(max_length=50, blank=True)


class Transfer(models.Model):
    class TransferType(models.TextChoices):
        PICKUP = 'PICKUP', _('Pickup')
        DROPOFF = 'DROPOFF', _('Dropoff')

    student_profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TransferType.choices)
    datetime = models.DateTimeField()
    flight_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)


class GeneratedDocument(models.Model):
    class DocType(models.TextChoices):
        CERTIFICATE = 'CERTIFICATE', _('Certificate')

    student_profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    doc_type = models.CharField(max_length=20, choices=DocType.choices)
    file = models.FileField(upload_to='generated/')
    created_at = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)


class AuditLog(models.Model):
    actor_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=64)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
