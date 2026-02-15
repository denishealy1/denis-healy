import csv
from io import TextIOWrapper
from datetime import timedelta
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from .models import Booking, Company, Placement, Project, StudentInvite, StudentProfile, Transfer, User


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email')


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'project_ref', 'start_date', 'end_date', 'destination_city', 'notes']


class InviteForm(forms.Form):
    emails = forms.CharField(widget=forms.Textarea, help_text='Comma/newline separated emails')

    def clean_emails(self):
        raw = self.cleaned_data['emails']
        emails = [e.strip().lower() for e in raw.replace(',', '\n').splitlines() if e.strip()]
        if not emails:
            raise forms.ValidationError('Provide at least one email')
        return list(dict.fromkeys(emails))


class CSVInviteUploadForm(forms.Form):
    csv_file = forms.FileField()

    def parse_rows(self):
        csv_file = self.cleaned_data['csv_file']
        text = TextIOWrapper(csv_file.file, encoding='utf-8')
        reader = csv.DictReader(text)
        return list(reader)


class StudentSignupForm(forms.Form):
    email = forms.EmailField(disabled=True)
    password = forms.CharField(widget=forms.PasswordInput)


class StudentProfileForm(forms.ModelForm):
    sector_preferences = forms.MultipleChoiceField(
        choices=StudentProfile.SECTOR_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = StudentProfile
        fields = [
            'first_name', 'last_name', 'nationality', 'phone', 'language_level',
            'sector_preferences', 'skills', 'cv_file', 'id_file', 'flight_number', 'arrival_time'
        ]


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'sector', 'address', 'contact_name', 'contact_email', 'capacity', 'verified', 'notes']


class PlacementForm(forms.ModelForm):
    class Meta:
        model = Placement
        fields = ['company', 'role_title', 'start_date', 'end_date', 'supervisor_name', 'supervisor_email', 'status']


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['unit', 'check_in', 'check_out', 'room_label']


class TransferForm(forms.ModelForm):
    class Meta:
        model = Transfer
        fields = ['type', 'datetime', 'flight_number', 'notes']
