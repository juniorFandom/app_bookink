from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ..models import Room, RoomType, RoomBooking
from ..serializers import (
    RoomSerializer, RoomTypeSerializer, 
    RoomBookingSerializer, RoomImageSerializer
)
from ..services import (
    RoomService, RoomTypeService, 
    BookingService, ReservationService
)


class RoomTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for room types."""
    queryset = RoomType.objects.filter(is_active=True)
    serializer_class = RoomTypeSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search room types by name or code."""
        query = request.query_params.get('q', '')
        if query:
            room_types = RoomTypeService.search_room_types(query)
            serializer = self.get_serializer(room_types, many=True)
            return Response(serializer.data)
        return Response([])

    @action(detail=True, methods=['get'])
    def rooms(self, request, pk=None):
        """Get all rooms of a specific room type."""
        room_type = self.get_object()
        rooms = Room.objects.filter(room_type=room_type, is_available=True)
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)


class RoomViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for rooms."""
    queryset = Room.objects.filter(is_available=True)
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter rooms based on query parameters."""
        queryset = Room.objects.filter(is_available=True)
        
        # Filter by business location
        business_location_id = self.request.query_params.get('business_location')
        if business_location_id:
            queryset = queryset.filter(business_location_id=business_location_id)
        
        # Filter by room type
        room_type_id = self.request.query_params.get('room_type')
        if room_type_id:
            queryset = queryset.filter(room_type_id=room_type_id)
        
        # Filter by max occupancy
        guests = self.request.query_params.get('guests')
        if guests:
            queryset = queryset.filter(max_occupancy__gte=guests)
        
        return queryset.select_related('room_type', 'business_location')

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available rooms for specific dates."""
        check_in_date = request.query_params.get('check_in_date')
        check_out_date = request.query_params.get('check_out_date')
        business_location_id = request.query_params.get('business_location')
        guests = request.query_params.get('guests', 1)
        
        if not all([check_in_date, check_out_date, business_location_id]):
            return Response(
                {'error': 'Missing required parameters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rooms = RoomService.get_available_rooms(
            business_location_id, check_in_date, check_out_date, guests
        )
        serializer = self.get_serializer(rooms, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        """Get all images for a specific room."""
        room = self.get_object()
        images = room.images.all().order_by('order')
        serializer = RoomImageSerializer(images, many=True)
        return Response(serializer.data)


class RoomBookingViewSet(viewsets.ModelViewSet):
    """API viewset for room bookings."""
    serializer_class = RoomBookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter bookings based on user and query parameters."""
        if self.request.user.is_staff:
            queryset = RoomBooking.objects.all()
        else:
            queryset = RoomBooking.objects.filter(customer=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related('room', 'room__room_type', 'customer', 'business_location')

    @action(detail=False, methods=['post'])
    def create_booking(self, request):
        """Create a new booking."""
        room_id = request.data.get('room_id')
        check_in_date = request.data.get('check_in_date')
        check_out_date = request.data.get('check_out_date')
        
        if not all([room_id, check_in_date, check_out_date]):
            return Response(
                {'error': 'Missing required parameters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        room = get_object_or_404(Room, id=room_id)
        
        try:
            booking = ReservationService.create_booking(
                room=room,
                customer=request.user,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                adults_count=request.data.get('adults_count', 1),
                children_count=request.data.get('children_count', 0),
                hotel_notes=request.data.get('hotel_notes', '')
            )
            serializer = self.get_serializer(booking)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking."""
        booking = self.get_object()
        reason = request.data.get('reason', 'Cancelled by user')
        
        try:
            cancelled_booking = ReservationService.cancel_booking(booking, reason)
            serializer = self.get_serializer(cancelled_booking)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            ) 