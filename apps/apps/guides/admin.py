"""Guide app admin configuration."""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import GuideProfile


@admin.register(GuideProfile)
class GuideProfileAdmin(admin.ModelAdmin):
    """Admin interface for guide profiles."""
    list_display = [
        'user',
        'business_location',
        'license_number',
        'years_of_experience',
        'hourly_rate',
        'is_verified',
        'created_at'
    ]
    list_filter = [
        'is_verified',
        'business_location',
        'created_at'
    ]
    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'license_number',
        'bio'
    ]
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    fieldsets = [
        (_('User Information'), {
            'fields': (
                'user',
                'business_location'
            )
        }),
        (_('Professional Information'), {
            'fields': (
                'license_number',
                'years_of_experience',
                'languages_spoken',
                'specializations',
                'hourly_rate'
            )
        }),
        (_('Verification'), {
            'fields': (
                'is_verified',
                'verification_document'
            )
        }),
        (_('Additional Information'), {
            'fields': (
                'bio',
            )
        }),
        (_('Timestamps'), {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    ]