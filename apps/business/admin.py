from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Business,
    BusinessLocation,
    BusinessLocationImage,
    BusinessReview,
    BusinessHours,
    SpecialBusinessHours,
    BusinessAmenityCategory,
    BusinessAmenity,
    BusinessAmenityAssignment
)

class BusinessLocationImageInline(admin.TabularInline):
    model = BusinessLocationImage
    extra = 1

class BusinessHoursInline(admin.TabularInline):
    model = BusinessHours
    extra = 7
    max_num = 7

class SpecialBusinessHoursInline(admin.TabularInline):
    model = SpecialBusinessHours
    extra = 1

class BusinessAmenityAssignmentInline(admin.TabularInline):
    model = BusinessAmenityAssignment
    extra = 1

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'is_verified', 'is_active']
    list_filter = ['is_verified', 'is_active']
    search_fields = ['name', 'description', 'owner__email']
    fieldsets = (
        (None, {
            'fields': ('name', 'owner', 'description')
        }),
        (_('Contact'), {
            'fields': ('email', 'phone', 'website')
        }),
        (_('Status'), {
            'fields': ('is_verified', 'is_active')
        }),
    )

@admin.register(BusinessLocation)
class BusinessLocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'business', 'business_location_type', 'is_main_location', 'is_verified', 'is_active']
    list_filter = ['business_location_type', 'is_main_location', 'is_verified', 'is_active']
    search_fields = ['name', 'business__name', 'description']
    inlines = [
        BusinessLocationImageInline,
        BusinessHoursInline,
        SpecialBusinessHoursInline,
        BusinessAmenityAssignmentInline,
    ]
    fieldsets = (
        (None, {
            'fields': ('business', 'name', 'business_location_type', 'description')
        }),
        (_('Contact'), {
            'fields': ('phone', 'email')
        }),
        (_('Registration'), {
            'fields': ('registration_number',)
        }),
        (_('Status'), {
            'fields': ('is_verified', 'is_active', 'featured', 'is_main_location')
        }),
    )

@admin.register(BusinessAmenityCategory)
class BusinessAmenityCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']

@admin.register(BusinessAmenity)
class BusinessAmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']

@admin.register(BusinessReview)
class BusinessReviewAdmin(admin.ModelAdmin):
    list_display = [
        'business_location',
        'reviewer',
        'overall_rating',
        'visit_date',
        'is_approved',
        'is_verified_purchase'
    ]
    list_filter = ['is_approved', 'is_verified_purchase', 'visit_type']
    search_fields = ['business_location__name', 'reviewer__email', 'title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('business_location', 'reviewer', 'title', 'content')
        }),
        (_('Ratings'), {
            'fields': (
                'overall_rating',
                'service_rating',
                'value_rating',
                'cleanliness_rating',
                'location_rating'
            )
        }),
        (_('Visit Details'), {
            'fields': ('visit_date', 'visit_type')
        }),
        (_('Status'), {
            'fields': ('is_approved', 'is_verified_purchase')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
