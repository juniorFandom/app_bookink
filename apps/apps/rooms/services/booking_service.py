from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from ..models import RoomBooking


class BookingService:
    """Service class for booking operations."""

    @staticmethod
    def get_user_bookings(user, status=None):
        """Get bookings for a specific user."""
        queryset = RoomBooking.objects.filter(customer=user)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')

    @staticmethod
    def get_booking_by_reference(reference):
        """Get booking by its reference."""
        try:
            return RoomBooking.objects.get(booking_reference=reference)
        except RoomBooking.DoesNotExist:
            return None

    @staticmethod
    def search_bookings(query, business_location=None):
        """Search bookings by various criteria."""
        queryset = RoomBooking.objects.all()
        
        if business_location:
            queryset = queryset.filter(business_location=business_location)
        
        if query:
            queryset = queryset.filter(
                Q(booking_reference__icontains=query) |
                Q(customer__email__icontains=query) |
                Q(room__room_number__icontains=query) |
                Q(room__room_type__name__icontains=query)
            )
        
        return queryset.select_related(
            'room', 'room__room_type', 'customer', 'business_location'
        ).order_by('-created_at')

    @staticmethod
    def get_bookings_for_date_range(business_location, start_date, end_date):
        """Get all bookings for a specific date range."""
        return RoomBooking.objects.filter(
            business_location=business_location,
            check_in_date__lte=end_date,
            check_out_date__gte=start_date
        ).select_related('room', 'customer').order_by('check_in_date')

    @staticmethod
    @transaction.atomic
    def update_booking_status(booking, new_status, notes=None):
        """Update booking status."""
        booking.status = new_status
        if notes:
            booking.hotel_notes = notes
        booking.updated_at = timezone.now()
        booking.save()
        return booking

    @staticmethod
    @transaction.atomic
    def update_payment_status(booking, payment_status):
        """Update booking payment status."""
        booking.payment_status = payment_status
        booking.updated_at = timezone.now()
        booking.save()
        return booking 