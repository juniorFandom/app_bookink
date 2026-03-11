from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from django.db.models import Avg, Count

from ..models import (
    Business,
    BusinessLocation,
    BusinessLocationImage,
    BusinessReview,
    BusinessHours,
    BusinessAmenityCategory,
    BusinessAmenity,
    BusinessAmenityAssignment
)
from ..serializers import (
    BusinessSerializer,
    BusinessDetailSerializer,
    BusinessLocationSerializer,
    BusinessLocationImageSerializer,
    BusinessHoursSerializer,
    BusinessReviewSerializer,
    BusinessAmenityCategorySerializer,
    BusinessAmenitySerializer,
    BusinessAmenityAssignmentSerializer
)
from ..services.services import (
    get_business_hours,
)

class BusinessViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing businesses
    """
    queryset = Business.objects.all()
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = ['is_verified', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            return queryset.filter(is_active=True)
        return queryset
    
    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return BusinessDetailSerializer
        return BusinessSerializer
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method not in permissions.SAFE_METHODS and obj.owner != request.user:
            raise PermissionDenied(_('You do not have permission to modify this business.'))
    
    @action(detail=True)
    def hours(self, request, pk=None):
        """
        Get business operating hours
        """
        business = self.get_object()
        hours = get_business_hours(business)
        return Response(hours)
    
    @action(detail=True)
    def statistics(self, request, pk=None):
        """
        Get business statistics (ratings, review count, etc.)
        """
        business = self.get_object()
        stats = BusinessReview.objects.filter(
            business=business,
            is_approved=True
        ).aggregate(
            avg_overall=Avg('overall_rating'),
            avg_service=Avg('service_rating'),
            avg_value=Avg('value_rating'),
            avg_cleanliness=Avg('cleanliness_rating'),
            avg_location=Avg('location_rating'),
            total_reviews=Count('id')
        )
        return Response(stats)

class BusinessLocationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing business locations
    """
    queryset = BusinessLocation.objects.all()
    serializer_class = BusinessLocationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = [
        'business',
        'business_location_type',
        'is_main_location',
        'is_verified',
        'is_active'
    ]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            return queryset.filter(is_active=True)
        return queryset
    
    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method not in permissions.SAFE_METHODS and obj.business.owner != request.user:
            raise PermissionDenied(_('You do not have permission to modify this location.'))
    
    @action(detail=True, methods=['post'])
    def upload_image(self, request, pk=None):
        """
        Upload an image for a business location
        """
        location = self.get_object()
        serializer = BusinessLocationImageSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(business_location=location)
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class BusinessReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing business reviews
    """
    serializer_class = BusinessReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['business', 'reviewer', 'visit_type', 'is_approved']
    ordering_fields = ['created_at', 'overall_rating']
    
    def get_queryset(self):
        return BusinessReview.objects.filter(
            is_approved=True
        ).select_related('reviewer', 'business')
    
    def perform_create(self, serializer):
        business = serializer.validated_data['business']
        if business.owner == self.request.user:
            raise PermissionDenied(_('You cannot review your own business.'))
        serializer.save(reviewer=self.request.user)
    
    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method not in permissions.SAFE_METHODS and obj.reviewer != request.user:
            raise PermissionDenied(_('You do not have permission to modify this review.'))

class BusinessAmenityCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing business amenity categories
    """
    queryset = BusinessAmenityCategory.objects.filter(is_active=True)
    serializer_class = BusinessAmenityCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['name']
    ordering = ['name']

class BusinessAmenityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing business amenities
    """
    queryset = BusinessAmenity.objects.filter(is_active=True)
    serializer_class = BusinessAmenitySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'description']
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def assign(self, request):
        """
        Assign amenities to a business location
        """
        location_id = request.data.get('location')
        amenities = request.data.get('amenities', [])
        
        try:
            location = BusinessLocation.objects.get(id=location_id)
        except BusinessLocation.DoesNotExist:
            return Response(
                {'error': _('Business location not found')},
                status=404
            )
        
        if location.business.owner != request.user:
            raise PermissionDenied(
                _('You do not have permission to modify this location\'s amenities.')
            )
        
        # Clear existing assignments
        BusinessAmenityAssignment.objects.filter(
            business_location=location
        ).delete()
        
        # Create new assignments
        for amenity_data in amenities:
            BusinessAmenityAssignment.objects.create(
                business_location=location,
                amenity_id=amenity_data['id'],
                details=amenity_data.get('details', ''),
                is_active=amenity_data.get('is_active', True)
            )
        
        return Response({'status': 'success'}) 