from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    VehicleCategory,
    Vehicle,
    VehicleImage,
    Driver,
    VehicleBooking
)

class VehicleImageInline(admin.TabularInline):
    model = VehicleImage
    extra = 1

@admin.register(VehicleCategory)
class VehicleCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'get_vehicle_count', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    ordering = ['name']
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'code', 'description', 'icon')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        })
    )

    def get_vehicle_count(self, obj):
        return obj.get_vehicle_count()
    get_vehicle_count.short_description = _('Vehicle Count')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = [
        'license_plate',
        'make',
        'model',
        'year',
        'vehicle_category',
        'passenger_capacity',
        'business_location',
        'is_available',
        'maintenance_mode',
        'mileage',
        'daily_rate',
    ]
    list_filter = [
        'vehicle_category',
        'business_location',
        'is_available',
        'maintenance_mode',
        'transmission',
        'fuel_type'
    ]
    search_fields = [
        'license_plate',
        'make',
        'model',
        'description'
    ]
    inlines = [VehicleImageInline]
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'business_location',
                'vehicle_category',
                'make',
                'model',
                'year',
                'license_plate',
                'color'
            )
        }),
        (_('Specifications'), {
            'fields': (
                'passenger_capacity',
                'transmission',
                'fuel_type',
                'mileage'
            )
        }),
        (_('Rental Information'), {
            'fields': (
                'daily_rate',
                'description',
                'features',
                'main_image'
            )
        }),
        (_('Status'), {
            'fields': (
                'is_available',
                'maintenance_mode'
            )
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        })
    )

@admin.register(VehicleImage)
class VehicleImageAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'caption', 'order', 'created_at']
    list_filter = ['vehicle']
    search_fields = ['caption', 'vehicle__license_plate']
    ordering = ['vehicle', 'order']
    readonly_fields = ['created_at']

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = [
        'full_name',
        'email',
        'phone_number',
        'license_number',
        'license_type',
        'business_location',
        'is_available',
        'is_verified',
        'years_of_experience',
    ]
    list_filter = [
        'business_location',
        'is_available',
        'is_verified',
        'license_type',
        'gender'
    ]
    search_fields = [
        'first_name',
        'last_name',
        'license_number',
        'phone_number',
        'email'
    ]
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (_('Personal Information'), {
            'fields': (
                'business_location',
                'user',
                'first_name',
                'last_name',
                'gender',
                'date_of_birth',
                'photo'
            )
        }),
        (_('Contact Information'), {
            'fields': (
                'phone_number',
                'email',
                'address'
            )
        }),
        (_('License Information'), {
            'fields': (
                'license_number',
                'license_type',
                'license_expiry',
                'years_of_experience'
            )
        }),
        (_('Additional Information'), {
            'fields': (
                'languages_spoken',
                'daily_rate',
                'verification_document'
            )
        }),
        (_('Status'), {
            'fields': (
                'is_available',
                'is_verified',
                'notes'
            )
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        })
    )

@admin.register(VehicleBooking)
class VehicleBookingAdmin(admin.ModelAdmin):
    list_display = [
        'booking_reference',
        'vehicle',
        'customer',
        'driver',
        'pickup_datetime',
        'return_datetime',
        'total_days',
        'status',
        'payment_status',
        'total_amount',
        'amount_paid',
    ]
    list_filter = [
        'status',
        'payment_status',
        'pickup_datetime',
        'return_datetime'
    ]
    search_fields = [
        'booking_reference',
        'vehicle__license_plate',
        'customer__email',
        'customer__first_name',
        'customer__last_name',
        'driver__first_name',
        'driver__last_name'
    ]
    readonly_fields = [
        'booking_reference',
        'created_at',
        'updated_at',
        'subtotal',
        'total_amount',
        'total_days'
    ]
    fieldsets = (
        (_('Booking Information'), {
            'fields': (
                'booking_reference',
                'vehicle',
                'customer',
                'driver',
                'pickup_datetime',
                'return_datetime'
            )
        }),
        (_('Location'), {
            'fields': (
                'pickup_location',
                'return_location'
            )
        }),
        (_('Financial Information'), {
            'fields': (
                'daily_rate',
                'total_days',
                'subtotal',
                'driver_fee',
                'additional_charges',
                'total_amount',
                'amount_paid'
            )
        }),
        (_('Status'), {
            'fields': (
                'status',
                'payment_status',
                'terms_accepted'
            )
        }),
        (_('Mileage'), {
            'fields': (
                'start_mileage',
                'end_mileage'
            )
        }),
        (_('Additional Information'), {
            'fields': (
                'notes',
                'created_at',
                'updated_at'
            )
        })
    )
