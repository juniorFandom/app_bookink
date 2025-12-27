from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import RoomType, Room, RoomImage, RoomBooking


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'max_occupancy', 'base_price', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(RoomImage)
class RoomImageAdmin(admin.ModelAdmin):
    list_display = ['room', 'caption', 'order', 'created_at']
    list_filter = ['room__room_type', 'room__business_location']
    search_fields = ['room__room_number', 'caption']
    ordering = ['room', 'order']


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = [
        'room_number', 'room_type', 'business_location',
        'price_per_night', 'is_available', 'maintenance_mode'
    ]
    list_filter = [
        'room_type', 'is_available', 'maintenance_mode',
        'business_location'
    ]
    search_fields = ['room_number', 'description']
    inlines = [RoomImageInline]
    raw_id_fields = ['business_location']


@admin.register(RoomBooking)
class RoomBookingAdmin(admin.ModelAdmin):
    list_display = [
        'booking_reference', 'room', 'customer',
        'check_in_date', 'check_out_date', 'status'
    ]
    list_filter = [
        'status', 'check_in_date',
        'check_out_date'
    ]
    search_fields = [
        'booking_reference', 'customer__email',
        'room__room_number'
    ]
    raw_id_fields = ['room', 'customer', 'business_location']
    readonly_fields = [
        'booking_reference', 'duration_nights',
        'commission_amount', 'cancelled_at',
        'created_at', 'updated_at'
    ]
