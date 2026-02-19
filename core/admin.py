from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import *


@admin.register(User)
class PortalUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'role', 'partner_org', 'is_staff')
    ordering = ('email',)
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('role', 'partner_org', 'preferred_language')}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {'fields': ('role', 'partner_org', 'preferred_language')}),)


admin.site.register(PartnerOrg)
admin.site.register(Project)
admin.site.register(StudentInvite)
admin.site.register(StudentProfile)
admin.site.register(Company)
admin.site.register(Placement)
admin.site.register(AccommodationUnit)
admin.site.register(Booking)
admin.site.register(Transfer)
admin.site.register(GeneratedDocument)
admin.site.register(AuditLog)
