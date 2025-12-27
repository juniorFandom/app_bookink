from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Avg
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from ..models import (
    Tour, TourDestination, TourDestinationImage,
    TourBooking, TourSchedule,
    TourReview
)
from ..serializers import (
    TourSerializer, TourDetailSerializer,
    TourDestinationSerializer, TourDestinationImageSerializer,
    TourBookingSerializer, TourScheduleSerializer, TourReviewSerializer
)
from ..services.tour_service import TourService

class TourViewSet(viewsets.ModelViewSet):
    """API endpoint for managing tours."""
    queryset = Tour.objects.filter(is_active=True)
    serializer_class = TourSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return TourDetailSerializer
        return TourSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by business location
        business_location = self.request.query_params.get('business_location')
        if business_location:
            queryset = queryset.filter(business_location=business_location)
        
        # Filter by tour type
        tour_type = self.request.query_params.get('tour_type')
        if tour_type:
            queryset = queryset.filter(tour_type=tour_type)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(price_per_person__gte=min_price)
        
        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price_per_person__lte=max_price)
        
        # Filter by duration
        min_duration = self.request.query_params.get('min_duration')
        if min_duration:
            queryset = queryset.filter(duration_days__gte=min_duration)
        
        max_duration = self.request.query_params.get('max_duration')
        if max_duration:
            queryset = queryset.filter(duration_days__lte=max_duration)
        
        # Filter by rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.annotate(
                avg_rating=Avg('tour_reviews__rating')
            ).filter(avg_rating__gte=min_rating)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(business_location=self.request.user.business_location)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, slug=None):
        """Get statistics for a tour."""
        tour = self.get_object()
        statistics = TourService.get_tour_statistics(tour)
        return Response(statistics)
    
    @action(detail=True, methods=['get'])
    def available_dates(self, request, slug=None):
        """Get available dates for a tour."""
        tour = self.get_object()
        available_dates = TourSchedule.objects.filter(
            tour=tour,
            status='SCHEDULED',
            start_datetime__gt=timezone.now()
        ).order_by('start_datetime')
        
        serializer = TourScheduleSerializer(available_dates, many=True)
        return Response(serializer.data)

class TourDestinationViewSet(viewsets.ModelViewSet):
    """API endpoint for managing tour destinations."""
    queryset = TourDestination.objects.filter(is_active=True)
    serializer_class = TourDestinationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    
    def get_queryset(self):
        return TourDestination.objects.filter(tour__slug=self.kwargs['tour_slug'])
    
    def perform_create(self, serializer):
        tour = get_object_or_404(Tour, slug=self.kwargs['tour_slug'])
        serializer.save(tour=tour)

class TourDestinationImageViewSet(viewsets.ModelViewSet):
    """API endpoint for managing destination images."""
    queryset = TourDestinationImage.objects.all()
    serializer_class = TourDestinationImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return TourDestinationImage.objects.filter(
            destination__slug=self.kwargs['destination_slug']
        )
    
    def perform_create(self, serializer):
        destination = get_object_or_404(
            TourDestination,
            slug=self.kwargs['destination_slug']
        )
        serializer.save(destination=destination)

class TourBookingViewSet(viewsets.ModelViewSet):
    """API endpoint for managing tour bookings."""
    serializer_class = TourBookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return TourBooking.objects.all()
        return TourBooking.objects.filter(customer=self.request.user)
    
    def perform_create(self, serializer):
        tour = get_object_or_404(Tour, slug=self.kwargs['tour_slug'])
        try:
            booking = TourService.create_booking(
                tour=tour,
                customer=self.request.user,
                tour_schedule=serializer.validated_data['tour_schedule'],
                num_participants=serializer.validated_data['number_of_participants'],
                guide_notes=serializer.validated_data.get('guide_notes')
            )
            serializer.instance = booking
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class TourScheduleViewSet(viewsets.ModelViewSet):
    """API endpoint for managing tour schedules."""
    queryset = TourSchedule.objects.all()
    serializer_class = TourScheduleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return TourSchedule.objects.filter(tour__slug=self.kwargs['tour_slug'])

class TourReviewViewSet(viewsets.ModelViewSet):
    """API endpoint for managing tour reviews."""
    serializer_class = TourReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return TourReview.objects.filter(
            tour__slug=self.kwargs['tour_slug'],
            is_approved=True
        )
    
    def perform_create(self, serializer):
        tour = get_object_or_404(Tour, slug=self.kwargs['tour_slug'])
        
        # Check if user has completed a booking for this tour
        has_booking = TourBooking.objects.filter(
            tour=tour,
            customer=self.request.user,
            status='completed'
        ).exists()
        
        if not has_booking:
            return Response(
                {'error': _('You can only review tours you have completed.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user has already reviewed this tour
        existing_review = TourReview.objects.filter(
            tour=tour,
            reviewer=self.request.user
        ).first()
        
        if existing_review:
            return Response(
                {'error': _('You have already reviewed this tour.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save(tour=tour, reviewer=self.request.user) 