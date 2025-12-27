from django.db import transaction
from django.utils import timezone
from ..models import RoomBooking


class ReservationService:
    """Service class for room booking operations."""

    @staticmethod
    @transaction.atomic
    def create_booking(room, customer, check_in_date, check_out_date, **kwargs):
        """
        Create a new room booking.
        """
        # Calculate total nights and amount
        total_nights = (check_out_date - check_in_date).days
        total_amount = room.price_per_night * total_nights

        # Create booking
        booking = RoomBooking.objects.create(
            room=room,
            customer=customer,
            business_location=room.business_location,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            total_amount=total_amount,
            **kwargs
        )

        return booking

    @staticmethod
    @transaction.atomic
    def cancel_booking(booking, reason):
        """
        Cancel a room booking.
        """
        booking.status = 'CANCELLED'
        booking.cancellation_reason = reason
        booking.cancelled_at = timezone.now()
        booking.save()

        return booking 