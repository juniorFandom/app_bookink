from rest_framework import serializers
from .models import RoomType, Room, RoomImage, RoomBooking


class RoomTypeSerializer(serializers.ModelSerializer):
    """Serializer for room types."""
    
    class Meta:
        model = RoomType
        fields = '__all__'


class RoomImageSerializer(serializers.ModelSerializer):
    """Serializer for room images."""
    
    class Meta:
        model = RoomImage
        fields = ['id', 'image', 'caption', 'order']


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for rooms."""
    
    room_type = RoomTypeSerializer(read_only=True)
    images = RoomImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Room
        fields = '__all__'


class RoomBookingSerializer(serializers.ModelSerializer):
    """Serializer for room bookings."""
    
    room = RoomSerializer(read_only=True)
    
    class Meta:
        model = RoomBooking
        fields = '__all__'
        read_only_fields = [
            'booking_reference', 'duration_nights',
            'total_amount', 'commission_amount',
            'status', 'payment_status',
            'cancelled_at', 'created_at', 'updated_at'
        ] 