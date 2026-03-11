from typing import List, Optional
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from ..models import (
    Vehicle,
    VehicleCategory,
    Driver,
    VehicleBooking,
    VehicleImage
)
from django.db import transaction
from decimal import Decimal


class VehicleService:
    """Service class for managing vehicles."""

    @staticmethod
    def get_vehicle(pk):
        return Vehicle.objects.get(pk=pk)

    @staticmethod
    def create_vehicle(**kwargs):
        return Vehicle.objects.create(**kwargs)

    @staticmethod
    def update_vehicle(pk, **kwargs):
        Vehicle.objects.filter(pk=pk).update(**kwargs)
        return Vehicle.objects.get(pk=pk)

    @staticmethod
    def delete_vehicle(pk):
        Vehicle.objects.filter(pk=pk).delete()

    @staticmethod
    def search_available_vehicles(
        start_date: timezone.datetime,
        end_date: timezone.datetime,
        category: Optional[VehicleCategory] = None,
        passenger_capacity: Optional[int] = None,
        transmission: Optional[str] = None,
        max_daily_rate: Optional[float] = None
    ) -> List[Vehicle]:
        """
        Search for available vehicles based on criteria.
        
        Args:
            start_date: The rental start date
            end_date: The rental end date
            category: Optional vehicle category filter
            passenger_capacity: Optional minimum passenger capacity
            transmission: Optional transmission type
            max_daily_rate: Optional maximum daily rate
            
        Returns:
            List[Vehicle]: List of available vehicles matching criteria
        """
        # Base query for available vehicles
        query = Q(is_available=True, maintenance_mode=False)
        
        # Add category filter if specified
        if category:
            query &= Q(vehicle_category=category)
            
        # Add passenger capacity filter if specified
        if passenger_capacity:
            query &= Q(passenger_capacity__gte=passenger_capacity)
            
        # Add transmission filter if specified
        if transmission:
            query &= Q(transmission=transmission)
            
        # Add daily rate filter if specified
        if max_daily_rate:
            query &= Q(daily_rate__lte=max_daily_rate)
            
        # Get all vehicles matching the criteria
        vehicles = Vehicle.objects.filter(query)
        
        # Filter out vehicles with overlapping bookings
        available_vehicles = []
        for vehicle in vehicles:
            overlapping_bookings = VehicleBooking.objects.filter(
                vehicle=vehicle,
                status__in=['PENDING', 'CONFIRMED', 'PICKED_UP'],
                pickup_datetime__lt=end_date,
                return_datetime__gt=start_date
            )
            
            if not overlapping_bookings.exists():
                available_vehicles.append(vehicle)
                
        return available_vehicles

    @staticmethod
    def update_vehicle_status(
        vehicle: Vehicle,
        is_available: Optional[bool] = None,
        maintenance_mode: Optional[bool] = None
    ) -> Vehicle:
        """
        Update the status of a vehicle.
        
        Args:
            vehicle: The vehicle to update
            is_available: Whether the vehicle is available for rent
            maintenance_mode: Whether the vehicle is under maintenance
            
        Returns:
            Vehicle: The updated vehicle object
        """
        if is_available is not None:
            vehicle.is_available = is_available
            
        if maintenance_mode is not None:
            vehicle.maintenance_mode = maintenance_mode
            
            # If putting in maintenance, make unavailable
            if maintenance_mode:
                vehicle.is_available = False
                
        vehicle.save()
        return vehicle

    @staticmethod
    def update_vehicle_mileage(vehicle: Vehicle, new_mileage: int) -> Vehicle:
        """
        Update the mileage of a vehicle.
        
        Args:
            vehicle: The vehicle to update
            new_mileage: The new mileage value
            
        Returns:
            Vehicle: The updated vehicle object
            
        Raises:
            ValidationError: If the new mileage is invalid
        """
        if new_mileage < vehicle.mileage:
            raise ValidationError(
                _('New mileage cannot be less than current mileage.')
            )
            
        vehicle.mileage = new_mileage
        vehicle.save()
        return vehicle

    @staticmethod
    def get_vehicle_statistics(vehicle: Vehicle) -> dict:
        """
        Get booking statistics for a vehicle.
        
        Args:
            vehicle: The vehicle to get statistics for
            
        Returns:
            dict: Vehicle statistics
        """
        completed_bookings = vehicle.bookings.filter(status='RETURNED')
        
        total_bookings = completed_bookings.count()
        total_days_rented = sum(
            booking.total_days for booking in completed_bookings
        )
        total_revenue = sum(
            booking.total_amount for booking in completed_bookings
        )
        
        return {
            'total_bookings': total_bookings,
            'total_days_rented': total_days_rented,
            'total_revenue': total_revenue,
            'total_mileage': vehicle.mileage
        }

    @staticmethod
    def get_available_drivers(
        start_date: timezone.datetime,
        end_date: timezone.datetime,
        business_location: Optional[str] = None
    ) -> List[Driver]:
        """
        Get available drivers for a specific time period.
        
        Args:
            start_date: The booking start date
            end_date: The booking end date
            business_location: Optional business location filter
            
        Returns:
            List[Driver]: List of available drivers
        """
        query = Q(is_available=True, is_verified=True)
        
        if business_location:
            query &= Q(business_location=business_location)
            
        drivers = Driver.objects.filter(query)
        
        available_drivers = []
        for driver in drivers:
            overlapping_bookings = VehicleBooking.objects.filter(
                driver=driver,
                status__in=['PENDING', 'CONFIRMED', 'PICKED_UP'],
                pickup_datetime__lt=end_date,
                return_datetime__gt=start_date
            )
            
            if not overlapping_bookings.exists():
                available_drivers.append(driver)
                
        return available_drivers

    @staticmethod
    def add_vehicle_image(vehicle, image, caption='', order=0):
        return VehicleImage.objects.create(vehicle=vehicle, image=image, caption=caption, order=order)

    @staticmethod
    def remove_vehicle_image(image_id):
        VehicleImage.objects.filter(pk=image_id).delete()

    @staticmethod
    def list_vehicle_images(vehicle):
        return VehicleImage.objects.filter(vehicle=vehicle).order_by('order')


class VehicleCategoryService:
    @staticmethod
    def get_category(pk):
        return VehicleCategory.objects.get(pk=pk)

    @staticmethod
    def count_vehicles(category):
        return category.vehicles.count()

    @staticmethod
    def list_active_vehicles(category):
        return category.vehicles.filter(is_available=True)


class VehicleBookingService:
    """Service class for managing vehicle bookings."""

    @staticmethod
    @transaction.atomic
    def create_booking(
        customer,
        vehicle,
        pickup_datetime,
        return_datetime,
        pickup_location,
        return_location,
        driver=None,
        notes='',
        terms_accepted=True,
        daily_rate=None,
        driver_fee=None,
        additional_charges=None
    ):
        """
        Creates a new vehicle booking after validation.
        """
        if not daily_rate:
            daily_rate = vehicle.daily_rate
        
        booking_data = {
            'customer': customer,
            'vehicle': vehicle,
            'driver': driver,
            'pickup_datetime': pickup_datetime,
            'return_datetime': return_datetime,
            'pickup_location': pickup_location,
            'return_location': return_location,
            'daily_rate': daily_rate,
            'driver_fee': driver_fee if driver_fee is not None else Decimal('0'),
            'additional_charges': additional_charges if additional_charges is not None else Decimal('0'),
            'notes': notes,
            'terms_accepted': terms_accepted
        }

        # The model's save method will calculate totals and set status
        booking = VehicleBooking.objects.create(**booking_data)
        booking.full_clean()
        booking.save()
        
        return booking

    @staticmethod
    def cancel_booking(booking: VehicleBooking):
        """
        Cancels a booking.
        """
        booking.cancel_booking()
        return booking

    @staticmethod
    def start_booking(booking: VehicleBooking):
        """
        Marks a booking as started (vehicle picked up).
        """
        booking.start_booking()
        return booking

    @staticmethod
    def complete_booking(booking: VehicleBooking, end_mileage: int):
        """
        Completes a booking (vehicle returned).
        """
        booking.complete_booking(end_mileage)
        return booking

    @staticmethod
    def process_payment(booking: VehicleBooking, amount: Decimal):
        """
        Process a payment for a booking.

        Args:
            booking: The booking to process payment for.
            amount: The amount to be paid.
        """
        if amount <= 0:
            raise ValidationError(_("Payment amount must be positive."))

        booking.amount_paid += amount
        booking.save(update_fields=['amount_paid', 'payment_status', 'updated_at'])
        return booking 