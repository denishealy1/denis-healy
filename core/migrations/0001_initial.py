# Generated manually for MVP bootstrap
import django.core.validators
import django.db.models.deletion
import core.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccommodationUnit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('type', models.CharField(choices=[('RESIDENCE', 'Residence'), ('APARTMENT', 'Apartment')], max_length=20)),
                ('address', models.CharField(max_length=255)),
                ('notes', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('sector', models.CharField(max_length=120)),
                ('address', models.CharField(max_length=255)),
                ('contact_name', models.CharField(max_length=120)),
                ('contact_email', models.EmailField(max_length=254)),
                ('capacity', models.IntegerField(default=1)),
                ('verified', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='PartnerOrg',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('country', models.CharField(blank=True, max_length=120)),
                ('contact_email', models.EmailField(blank=True, max_length=254)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('project_ref', models.CharField(max_length=100)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('destination_city', models.CharField(default='Malaga', max_length=120)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('partner_org', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='core.partnerorg')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(auto_now_add=True, verbose_name='date joined')),
                ('username', models.CharField(max_length=255, unique=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('role', models.CharField(choices=[('ADMIN', 'Admin'), ('PARTNER', 'Partner'), ('STUDENT', 'Student')], default='STUDENT', max_length=20)),
                ('preferred_language', models.CharField(choices=[('en', 'English'), ('es', 'Español')], default='en', max_length=2)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('partner_org', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.partnerorg')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
            managers=[
                ('objects', core.models.PortalUserManager()),
            ],
        ),
        migrations.CreateModel(
            name='StudentProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('nationality', models.CharField(blank=True, max_length=120)),
                ('phone', models.CharField(blank=True, max_length=50)),
                ('language_level', models.CharField(choices=[('A1', 'A1'), ('A2', 'A2'), ('B1', 'B1'), ('B2', 'B2'), ('C1', 'C1'), ('C2', 'C2')], default='A1', max_length=2)),
                ('sector_preferences', models.JSONField(blank=True, default=list)),
                ('skills', models.TextField(blank=True)),
                ('cv_file', models.FileField(blank=True, upload_to='cv/', validators=[django.core.validators.FileExtensionValidator(['pdf']), core.models.validate_file_size])),
                ('id_file', models.FileField(blank=True, upload_to='id/', validators=[django.core.validators.FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png']), core.models.validate_file_size])),
                ('flight_number', models.CharField(blank=True, max_length=50)),
                ('arrival_time', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('INVITED', 'Invited'), ('ONBOARDING', 'Onboarding'), ('ONBOARDED', 'Onboarded')], default='ONBOARDING', max_length=20)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='students', to='core.project')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='student_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Transfer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('PICKUP', 'Pickup'), ('DROPOFF', 'Dropoff')], max_length=20)),
                ('datetime', models.DateTimeField()),
                ('flight_number', models.CharField(blank=True, max_length=50)),
                ('notes', models.TextField(blank=True)),
                ('student_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transfers', to='core.studentprofile')),
            ],
        ),
        migrations.CreateModel(
            name='StudentInvite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('token', models.CharField(max_length=64, unique=True)),
                ('expires_at', models.DateTimeField()),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invites', to='core.project')),
            ],
            options={
                'unique_together': {('project', 'email')},
            },
        ),
        migrations.CreateModel(
            name='Placement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_title', models.CharField(max_length=255)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('supervisor_name', models.CharField(max_length=120)),
                ('supervisor_email', models.EmailField(max_length=254)),
                ('status', models.CharField(choices=[('PROPOSED', 'Proposed'), ('CONFIRMED', 'Confirmed'), ('ACTIVE', 'Active'), ('COMPLETED', 'Completed')], default='PROPOSED', max_length=20)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.company')),
                ('student_profile', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='placement', to='core.studentprofile')),
            ],
        ),
        migrations.CreateModel(
            name='GeneratedDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doc_type', models.CharField(choices=[('CERTIFICATE', 'Certificate')], max_length=20)),
                ('file', models.FileField(upload_to='generated/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('meta', models.JSONField(blank=True, default=dict)),
                ('student_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='core.studentprofile')),
            ],
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('check_in', models.DateField()),
                ('check_out', models.DateField()),
                ('room_label', models.CharField(blank=True, max_length=50)),
                ('student_profile', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='booking', to='core.studentprofile')),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.accommodationunit')),
            ],
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=120)),
                ('entity_type', models.CharField(max_length=120)),
                ('entity_id', models.CharField(max_length=64)),
                ('details', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ip', models.GenericIPAddressField(blank=True, null=True)),
                ('actor_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
