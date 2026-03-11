from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Tour,
    TourDestination,
    TourDestinationImage,
    TourBooking,
    TourSchedule,
    TourReview
)


class DestinationImageInline(admin.TabularInline):
    model = TourDestinationImage
    extra = 1


class TourDestinationInline(admin.TabularInline):
    model = TourDestination
    extra = 1
    fields = ['name', 'day_number', 'duration', 'is_active']


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = [
        'nom_balade',
        'business_location',
        'type',
        'duree',
        'prix_par_personne',
        'is_active'
    ]
    list_filter = [
        'type',
        'is_active',
        'business_location'
    ]
    search_fields = [
        'nom_balade',
        'description',
        'business_location__name'
    ]
    prepopulated_fields = {'slug': ('nom_balade',)}
    inlines = [
        TourDestinationInline
    ]
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'business_location',
                'nom_balade',
                'slug',
                'description',
                'type'
            )
        }),
        (_('Pricing & Capacity'), {
            'fields': (
                'prix_par_personne',
                'nombre_participant_min',
                'nombre_participant_max',
                'duree'
            )
        }),
        (_('Media'), {
            'fields': ('image',)
        }),
        (_('Schedule'), {
            'fields': ('date_debut', 'heure_depart')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        })
    )


class TourDestinationImageInline(admin.TabularInline):
    model = TourDestinationImage
    extra = 1
    fields = ['image', 'caption', 'order']


@admin.register(TourDestination)
class TourDestinationAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'tour',
        'day_number',
        'duration',
        'is_active',
        'is_featured'
    ]
    list_filter = ['is_active', 'is_featured', 'tour']
    search_fields = ['name', 'description', 'city', 'region']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [TourDestinationImageInline]
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('tour', 'name', 'slug', 'description')
        }),
        (_('Location'), {
            'fields': ('address', 'city', 'region', 'country', 'postal_code', 'latitude', 'longitude')
        }),
        (_('Tour Details'), {
            'fields': ('day_number', 'duration', 'highlights', 'features')
        }),
        (_('Additional Information'), {
            'fields': ('best_time_to_visit', 'climate', 'how_to_get_there')
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_featured')
        })
    )


@admin.register(TourBooking)
class TourBookingAdmin(admin.ModelAdmin):
    list_display = [
        'booking_reference',
        'tour_schedule',
        'customer',
        'number_of_participants',
        'status',
        'created_at'
    ]
    list_filter = [
        'status',
        'tour_schedule',
        'created_at'
    ]
    search_fields = [
        'booking_reference',
        'customer__email',
        'customer__first_name',
        'customer__last_name'
    ]
    readonly_fields = [
        'booking_reference',
        'created_at',
        'updated_at'
    ]
    fieldsets = (
        (_('Booking Information'), {
            'fields': ('booking_reference', 'tour_schedule', 'customer', 'number_of_participants')
        }),
        (_('Schedule'), {
            'fields': ('start_date', 'end_date')
        }),
        (_('Status & Notes'), {
            'fields': ('status', 'guide_notes')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        })
    )


@admin.register(TourSchedule)
class TourScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'tour',
        'start_datetime',
        'end_datetime',
        'available_spots',
        'status'
    ]
    list_filter = [
        'status',
        'tour',
        'start_datetime'
    ]
    search_fields = [
        'tour__name',
        'cancellation_reason'
    ]
    fieldsets = (
        (_('Schedule Information'), {
            'fields': ('tour', 'tour_booking', 'start_datetime', 'end_datetime')
        }),
        (_('Capacity & Pricing'), {
            'fields': ('available_spots', 'price_override')
        }),
        (_('Status'), {
            'fields': ('status', 'cancellation_reason')
        })
    )


@admin.register(TourReview)
class TourReviewAdmin(admin.ModelAdmin):
    list_display = [
        'tour',
        'reviewer',
        'rating',
        'guide_rating',
        'value_rating',
        'created_at'
    ]
    list_filter = [
        'rating',
        'guide_rating',
        'value_rating',
        'created_at'
    ]
    search_fields = [
        'tour__name',
        'reviewer__email',
        'reviewer__first_name',
        'reviewer__last_name',
        'content'
    ]
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    fieldsets = (
        (_('Review Information'), {
            'fields': ('tour', 'reviewer', 'booking', 'content')
        }),
        (_('Ratings'), {
            'fields': ('rating', 'guide_rating', 'value_rating', 'activities_rating',
                      'transportation_rating', 'accommodation_rating', 'food_rating')
        }),
        (_('Additional Information'), {
            'fields': ('pros', 'cons', 'tips', 'would_recommend')
        }),
        (_('Status'), {
            'fields': ('is_approved', 'is_verified_purchase')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        })
    )
