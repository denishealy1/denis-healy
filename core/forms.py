import csv
from io import StringIO

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import (
    AccommodationUnit,
    Booking,
    Company,
    Placement,
    Project,
    StudentProfile,
    Transfer,
    User,
)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'project_ref', 'start_date', 'end_date', 'destination_city', 'notes']


class InviteForm(forms.Form):
    emails = forms.CharField(widget=forms.Textarea, help_text=_('Comma or newline separated emails'))

    def clean_emails(self):
        raw = self.cleaned_data['emails']
        emails = [item.strip() for item in raw.replace(',', '\n').splitlines() if item.strip()]
        if not emails:
            raise ValidationError(_('Add at least one email'))
        return list(dict.fromkeys(emails))


class InviteCSVForm(forms.Form):
    csv_file = forms.FileField()

    def parse(self):
        data = self.cleaned_data['csv_file'].read().decode('utf-8')
        reader = csv.DictReader(StringIO(data))
        required = {'first_name', 'last_name', 'email', 'arrival_date', 'departure_date'}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValidationError(_('Invalid CSV headers'))
        return list(reader)


class InviteAcceptForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email',)


class StudentProfileForm(forms.ModelForm):
    sector_preferences = forms.MultipleChoiceField(
        choices=StudentProfile.SECTOR_CHOICES,
        widget=forms.CheckboxSelectMultiple,
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
        fields = '__all__'


class PlacementForm(forms.ModelForm):
    class Meta:
        model = Placement
        exclude = ('student_profile',)


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        exclude = ('student_profile',)


class TransferForm(forms.ModelForm):
    class Meta:
        model = Transfer
        exclude = ('student_profile',)


class AccommodationUnitForm(forms.ModelForm):
    class Meta:
        model = AccommodationUnit
        fields = '__all__'
