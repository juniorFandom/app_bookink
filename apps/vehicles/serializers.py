from rest_framework import serializers
from .models import (
    VehicleCategory,
    Vehicle,
    VehicleImage,
    Driver,
    VehicleBooking
)
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class VehicleCategorySerializer(serializers.ModelSerializer):
    """Serializer for the VehicleCategory model."""
    vehicle_count = serializers.SerializerMethodField()

    class Meta:
        model = VehicleCategory
        fields = [
            'id',
            'name',
            'code',
            'description',
            'icon',
            'is_active',
            'vehicle_count'
        ]
    
    def get_vehicle_count(self, obj):
        return obj.get_vehicle_count()


class VehicleImageSerializer(serializers.ModelSerializer):
    """Serializer for the VehicleImage model."""

    class Meta:
        model = VehicleImage
        fields = ['id', 'image', 'caption', 'order']


class VehicleSerializer(serializers.ModelSerializer):
    """Serializer for the Vehicle model."""
    
    vehicle_category = serializers.StringRelatedField()
    business_location = serializers.StringRelatedField()
    images = VehicleImageSerializer(many=True, read_only=True)
    display_name = serializers.CharField(source='get_display_name', read_only=True)
    rentable = serializers.BooleanField(source='is_rentable', read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'id',
            'business_location',
            'vehicle_category',
            'make',
            'model',
            'year',
            'display_name',
            'license_plate',
            'color',
            'passenger_capacity',
            'transmission',
            'fuel_type',
            'daily_rate',
            'description',
            'features',
            'main_image',
            'mileage',
            'is_available',
            'maintenance_mode',
            'rentable',
            'images',
        ]
        read_only_fields = ['display_name', 'rentable']


class DriverSerializer(serializers.ModelSerializer):
    """Serializer for the Driver model."""

    user = serializers.StringRelatedField()
    business_location = serializers.StringRelatedField()
    full_name = serializers.CharField(source='full_name', read_only=True)
    license_is_valid = serializers.BooleanField(source='is_license_valid', read_only=True)

    class Meta:
        model = Driver
        fields = [
            'id',
            'business_location',
            'user',
            'first_name',
            'last_name',
            'full_name',
            'gender',
            'date_of_birth',
            'phone_number',
            'email',
            'address',
            'license_number',
            'license_type',
            'license_expiry',
            'license_is_valid',
            'photo',
            'years_of_experience',
            'languages_spoken',
            'daily_rate',
            'is_available',
            'is_verified',
            'notes'
        ]
        read_only_fields = ['full_name', 'license_is_valid']


class VehicleBookingSerializer(serializers.ModelSerializer):
    """Serializer for the VehicleBooking model."""
    
    customer = serializers.StringRelatedField()
    vehicle = VehicleSerializer(read_only=True)
    driver = DriverSerializer(read_only=True)
    
    vehicle_id = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(), source='vehicle', write_only=True
    )
    driver_id = serializers.PrimaryKeyRelatedField(
        queryset=Driver.objects.all(), source='driver', write_only=True, required=False
    )

    class Meta:
        model = VehicleBooking
        fields = [
            'id',
            'booking_reference',
            'customer',
            'vehicle',
            'vehicle_id',
            'driver',
            'driver_id',
            'pickup_datetime',
            'return_datetime',
            'pickup_location',
            'return_location',
            'status',
            'payment_status',
            'daily_rate',
            'total_days',
            'subtotal',
            'driver_fee',
            'additional_charges',
            'total_amount',
            'amount_paid',
            'start_mileage',
            'end_mileage',
            'notes',
            'terms_accepted',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'booking_reference',
            'status',
            'payment_status',
            'total_days',
            'subtotal',
            'total_amount',
            'created_at',
            'updated_at',
        ]

    def validate(self, data):
        """
        Check that the pickup is before the return.
        Check that the vehicle is available.
        """
        pickup_datetime = data.get('pickup_datetime')
        return_datetime = data.get('return_datetime')
        vehicle = data.get('vehicle')

        if pickup_datetime and return_datetime:
            if pickup_datetime >= return_datetime:
                raise serializers.ValidationError({
                    'return_datetime': _('Return datetime must be after pickup datetime.')
                })
            
            if pickup_datetime < timezone.now():
                raise serializers.ValidationError({
                    'pickup_datetime': _('Pickup datetime cannot be in the past.')
                })

        if vehicle:
            overlapping_bookings = VehicleBooking.objects.filter(
                vehicle=vehicle,
                status__in=['PENDING', 'CONFIRMED', 'PICKED_UP'],
                pickup_datetime__lt=return_datetime,
                return_datetime__gt=pickup_datetime
            )
            
            if self.instance:
                overlapping_bookings = overlapping_bookings.exclude(pk=self.instance.pk)

            if overlapping_bookings.exists():
                raise serializers.ValidationError(
                    _('Vehicle is not available for the selected dates.')
                )
        
        return data

    def create(self, validated_data):
        validated_data['customer'] = self.context['request'].user
        return super().create(validated_data) 