from datetime import date, datetime, timedelta
from typing import List, Dict
from django.db.models import Q, Avg, Count
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from ..models import Tour, TourBooking, TourSchedule, TourDestination, TourReview


class TourService:
    """Service class for managing tours."""

    @staticmethod
    def search_available_tours(
        start_date: date,
        num_participants: int,
        max_price: float = None,
        duration_days: int = None,
        tour_type: str = None
    ) -> List[Tour]:
        """
        Search for available tours based on criteria.
        
        Args:
            start_date: The desired start date
            num_participants: Number of participants
            max_price: Optional maximum price per person
            duration_days: Optional desired duration in days
            tour_type: Optional tour type filter
            
        Returns:
            List[Tour]: List of available tours matching criteria
        """
        # Base query for active tours
        query = Q(is_active=True)
        
        # Add participant filter
        query &= Q(
            min_participants__lte=num_participants,
            max_participants__gte=num_participants
        )
        
        # Add price filter if specified
        if max_price:
            query &= Q(price_per_person__lte=max_price)
            
        # Add duration filter if specified
        if duration_days:
            query &= Q(duration_days=duration_days)
            
        # Add tour type filter if specified
        if tour_type:
            query &= Q(tour_type=tour_type)
            
        # Get all tours matching the criteria
        tours = Tour.objects.filter(query)
        
        # Filter out tours with conflicting bookings
        available_tours = []
        for tour in tours:
            end_date = start_date + tour.duration_days
            conflicting_bookings = tour.bookings.filter(
                status__in=['CONFIRMED', 'IN_PROGRESS'],
                start_date__lt=end_date,
                end_date__gt=start_date
            )
            
            if not conflicting_bookings.exists():
                available_tours.append(tour)
                
        return available_tours

    @staticmethod
    def get_tour_availability(
        tour: Tour,
        start_date: date,
        num_participants: int
    ) -> Dict:
        """
        Check tour availability for given date and participants.
        
        Args:
            tour: The tour to check
            start_date: The desired start date
            num_participants: Number of participants
            
        Returns:
            dict: Availability status and details
        """
        if not tour.is_active:
            return {
                'is_available': False,
                'reason': _('Tour is not currently active.')
            }
            
        if not (tour.min_participants <= num_participants <= tour.max_participants):
            return {
                'is_available': False,
                'reason': _(
                    'Number of participants must be between %(min)d and %(max)d.'
                ) % {
                    'min': tour.min_participants,
                    'max': tour.max_participants
                }
            }
            
        end_date = start_date + tour.duration_days
        conflicting_bookings = tour.bookings.filter(
            status__in=['CONFIRMED', 'IN_PROGRESS'],
            start_date__lt=end_date,
            end_date__gt=start_date
        )
        
        if conflicting_bookings.exists():
            return {
                'is_available': False,
                'reason': _('Tour is not available for the selected dates.')
            }
            
        return {
            'is_available': True,
            'start_date': start_date,
            'end_date': end_date,
            'price_info': tour.calculate_total_price(num_participants)
        }

    @staticmethod
    def check_tour_availability(tour: Tour, start_date: datetime,
                              num_participants: int) -> bool:
        """
        Check if a tour is available for the given date and number of participants.
        
        Args:
            tour: The tour to check
            start_date: The tour start date
            num_participants: Number of participants
            
        Returns:
            bool: True if tour is available, False otherwise
        """
        if not tour.is_active:
            return False

        if num_participants < tour.min_participants:
            return False

        if num_participants > tour.max_participants:
            return False

        end_date = start_date + timedelta(days=tour.duration_days - 1)
        
        overlapping_bookings = TourBooking.objects.filter(
            tour=tour,
            status__in=['pending', 'confirmed', 'in_progress'],
            start_date__lt=end_date,
            end_date__gt=start_date
        )
        
        return not overlapping_bookings.exists()

    @staticmethod
    def calculate_tour_price(tour: Tour, num_participants: int,
                           selected_activities: list = None) -> dict:
        """
        Calculate the total price for a tour booking.
        
        Args:
            tour: The tour to calculate price for
            num_participants: Number of participants
            selected_activities: Optional list of additional activities
            
        Returns:
            dict: Breakdown of tour costs
        """
        base_price = tour.price_per_person * num_participants
        activities_price = sum(
            activity.calculate_total_price(num_participants)
            for activity in (selected_activities or [])
        )
        
        return {
            'base_price': base_price,
            'activities_price': activities_price,
            'total_price': base_price + activities_price
        }

    @staticmethod
    @transaction.atomic
    def create_booking(tour: Tour, customer, start_date: datetime,
                      num_participants: int, selected_activities: list = None,
                      guide_notes: str = None) -> TourBooking:
        """
        Create a new tour booking.
        
        Args:
            tour: The tour to book
            customer: The customer making the booking
            start_date: The tour start date
            num_participants: Number of participants
            selected_activities: Optional list of additional activities
            guide_notes: Optional notes for the guide
            
        Returns:
            TourBooking: The created booking object
            
        Raises:
            ValidationError: If the booking cannot be created
        """
        # Validate dates
        if start_date < timezone.now():
            raise ValidationError(_('Start date cannot be in the past.'))
        
        end_date = start_date + timedelta(days=tour.duration_days - 1)

        # Check availability
        if not TourService.check_tour_availability(tour, start_date, num_participants):
            raise ValidationError(_('Tour is not available for these dates and number of participants.'))

        # Calculate costs
        costs = TourService.calculate_tour_price(tour, num_participants, selected_activities)

        # Create booking
        booking = TourBooking.objects.create(
            tour=tour,
            customer=customer,
            start_date=start_date,
            end_date=end_date,
            number_of_participants=num_participants,
            guide_notes=guide_notes,
            base_price=costs['base_price'],
            activities_price=costs['activities_price'],
            total_amount=costs['total_price']
        )

        # Create schedule
        TourSchedule.objects.create(
            tour=tour,
            tour_booking=booking,
            start_datetime=start_date,
            end_datetime=end_date,
            available_spots=tour.max_participants - num_participants,
            status='SCHEDULED'
        )

        return booking

    @staticmethod
    @transaction.atomic
    def update_booking_status(booking: TourBooking, new_status: str) -> TourBooking:
        """
        Update the status of a tour booking.
        
        Args:
            booking: The booking to update
            new_status: The new status
            
        Returns:
            TourBooking: The updated booking object
            
        Raises:
            ValidationError: If the status cannot be updated
        """
        valid_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled'],
            'completed': [],
            'cancelled': []
        }

        if new_status not in valid_transitions.get(booking.status, []):
            raise ValidationError(
                _('Invalid status transition from %(current)s to %(new)s') % {
                    'current': booking.status,
                    'new': new_status
                }
            )

        booking.status = new_status
        booking.save()

        # Update schedule status
        schedule = booking.tour_schedules.first()
        if schedule:
            schedule.status = new_status
            schedule.save()

        return booking

    @staticmethod
    def get_available_tours(start_date: datetime, num_participants: int):
        """
        Get all tours available for booking in the given period.
        
        Args:
            start_date: The tour start date
            num_participants: Number of participants
            
        Returns:
            QuerySet: Available tours
        """
        return Tour.objects.filter(
            is_active=True,
            min_participants__lte=num_participants,
            max_participants__gte=num_participants
        ).exclude(
            tour_bookings__status__in=['pending', 'confirmed', 'in_progress'],
            tour_bookings__start_date__lt=start_date + timedelta(days=F('duration_days') - 1),
            tour_bookings__end_date__gt=start_date
        )

    @staticmethod
    def process_booking_payment(booking: TourBooking, amount: Decimal) -> None:
        """
        Process a payment for a booking.
        
        Args:
            booking: The booking to process payment for
            amount: The payment amount
            
        Raises:
            ValidationError: If the payment cannot be processed
        """
        if amount <= 0:
            raise ValidationError(_('Payment amount must be greater than zero.'))

        booking.amount_paid += amount
        
        if booking.amount_paid >= booking.total_amount:
            booking.payment_status = 'PAID'
        elif booking.amount_paid > 0:
            booking.payment_status = 'PARTIALLY_PAID'
        
        booking.save()

    @staticmethod
    def get_tour_statistics(tour: Tour) -> dict:
        """
        Get statistics for a tour.
        
        Args:
            tour: The tour to get statistics for
            
        Returns:
            dict: Tour statistics
        """
        reviews = TourReview.objects.filter(tour=tour, is_approved=True)
        total_reviews = reviews.count()
        
        if total_reviews == 0:
            return {
                'total_reviews': 0,
                'average_rating': 0,
                'rating_breakdown': {},
                'recommendation_rate': 0
            }
        
        ratings = {
            'overall': reviews.aggregate(avg=Avg('rating'))['avg'],
            'guide': reviews.aggregate(avg=Avg('guide_rating'))['avg'],
            'value': reviews.aggregate(avg=Avg('value_rating'))['avg'],
            'activities': reviews.aggregate(avg=Avg('activities_rating'))['avg'],
            'transportation': reviews.aggregate(avg=Avg('transportation_rating'))['avg'],
            'accommodation': reviews.aggregate(avg=Avg('accommodation_rating'))['avg'],
            'food': reviews.aggregate(avg=Avg('food_rating'))['avg']
        }
        
        rating_breakdown = {
            '5': reviews.filter(rating=5).count(),
            '4': reviews.filter(rating=4).count(),
            '3': reviews.filter(rating=3).count(),
            '2': reviews.filter(rating=2).count(),
            '1': reviews.filter(rating=1).count()
        }
        
        recommendation_rate = (
            reviews.filter(would_recommend=True).count() / total_reviews * 100
        )
        
        return {
            'total_reviews': total_reviews,
            'average_rating': ratings['overall'],
            'rating_breakdown': rating_breakdown,
            'recommendation_rate': recommendation_rate,
            'detailed_ratings': ratings
        }

    @staticmethod
    def search_tours(query=None, tour_type=None, min_price=None, max_price=None,
                    min_duration=None, max_duration=None, min_rating=None,
                    verified_only=False):
        """Search for tours based on various criteria."""
        queryset = Tour.objects.filter(is_active=True)

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )

        if tour_type:
            queryset = queryset.filter(tour_type=tour_type)

        if min_price:
            queryset = queryset.filter(price_per_person__gte=min_price)

        if max_price:
            queryset = queryset.filter(price_per_person__lte=max_price)

        if min_duration:
            queryset = queryset.filter(duration_days__gte=min_duration)

        if max_duration:
            queryset = queryset.filter(duration_days__lte=max_duration)

        if min_rating:
            queryset = queryset.annotate(
                avg_rating=Avg('tour_reviews__rating')
            ).filter(avg_rating__gte=min_rating)

        if verified_only:
            queryset = queryset.filter(business_location__is_verified=True)

        return queryset

    @staticmethod
    def get_available_dates(tour, start_date=None, end_date=None):
        """Get available dates for a tour within a date range."""
        queryset = TourSchedule.objects.filter(
            tour=tour,
            status='SCHEDULED',
            start_datetime__gt=timezone.now()
        )

        if start_date:
            queryset = queryset.filter(start_datetime__gte=start_date)

        if end_date:
            queryset = queryset.filter(end_datetime__lte=end_date)

        return queryset.order_by('start_datetime')

    @staticmethod
    def get_tour_itinerary(tour):
        """Get the complete itinerary for a tour."""
        destinations = TourDestination.objects.filter(
            tour=tour,
            is_active=True
        ).order_by('day_number')

        itinerary = []
        for day in range(1, tour.duration_days + 1):
            day_destinations = destinations.filter(day_number=day)

            itinerary.append({
                'day': day,
                'destinations': day_destinations
            })

        return itinerary