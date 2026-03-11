from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Business,
    BusinessLocation,
    BusinessLocationImage,
    BusinessHours,
    BusinessReview,
    BusinessAmenityCategory,
    BusinessAmenity,
    BusinessAmenityAssignment
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user information in business-related contexts
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = fields

class BusinessLocationImageSerializer(serializers.ModelSerializer):
    """
    Serializer for business location images
    """
    class Meta:
        model = BusinessLocationImage
        fields = ['id', 'image', 'caption', 'is_primary']
        read_only_fields = ['id']

class BusinessHoursSerializer(serializers.ModelSerializer):
    """
    Serializer for business operating hours
    """
    day_name = serializers.CharField(source='get_day_display', read_only=True)
    
    class Meta:
        model = BusinessHours
        fields = [
            'id',
            'day',
            'day_name',
            'opening_time',
            'closing_time',
            'is_closed',
            'break_start',
            'break_end'
        ]
        read_only_fields = ['id']

class BusinessReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for business reviews
    """
    reviewer = UserSerializer(read_only=True)
    
    class Meta:
        model = BusinessReview
        fields = [
            'id',
            'business',
            'reviewer',
            'title',
            'content',
            'overall_rating',
            'service_rating',
            'value_rating',
            'cleanliness_rating',
            'location_rating',
            'visit_date',
            'visit_type',
            'is_approved',
            'is_verified_purchase',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'reviewer', 'created_at', 'updated_at']

class BusinessAmenityCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for business amenity categories
    """
    class Meta:
        model = BusinessAmenityCategory
        fields = ['id', 'name', 'description', 'icon', 'is_active']
        read_only_fields = fields

class BusinessAmenitySerializer(serializers.ModelSerializer):
    """
    Serializer for business amenities
    """
    category = BusinessAmenityCategorySerializer(read_only=True)
    
    class Meta:
        model = BusinessAmenity
        fields = ['id', 'category', 'name', 'description', 'icon', 'is_active']
        read_only_fields = fields

class BusinessAmenityAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer for business amenity assignments
    """
    amenity = BusinessAmenitySerializer(read_only=True)
    amenity_id = serializers.PrimaryKeyRelatedField(
        queryset=BusinessAmenity.objects.all(),
        write_only=True
    )
    
    class Meta:
        model = BusinessAmenityAssignment
        fields = [
            'id',
            'amenity',
            'amenity_id',
            'details',
            'is_active'
        ]
        read_only_fields = ['id', 'amenity']
    
    def create(self, validated_data):
        amenity = validated_data.pop('amenity_id')
        return BusinessAmenityAssignment.objects.create(
            amenity=amenity,
            **validated_data
        )

class BusinessLocationSerializer(serializers.ModelSerializer):
    """
    Serializer for business locations
    """
    images = BusinessLocationImageSerializer(many=True, read_only=True)
    business_hours = BusinessHoursSerializer(many=True, read_only=True)
    amenities = BusinessAmenityAssignmentSerializer(
        source='businessamenityassignment_set',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = BusinessLocation
        fields = [
            'id',
            'business',
            'name',
            'business_location_type',
            'phone',
            'email',
            'registration_number',
            'description',
            'founded_date',
            'is_main_location',
            'is_verified',
            'is_active',
            'featured',
            'images',
            'business_hours',
            'amenities'
        ]
        read_only_fields = ['id', 'is_verified']

class BusinessSerializer(serializers.ModelSerializer):
    """
    Serializer for basic business information (list view)
    """
    owner = UserSerializer(read_only=True)
    locations = BusinessLocationSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Business
        fields = [
            'id',
            'name',
            'owner',
            'email',
            'phone',
            'website',
            'description',
            'founded_date',
            'is_verified',
            'is_active',
            'locations',
            'average_rating',
            'review_count'
        ]
        read_only_fields = ['id', 'owner', 'is_verified']

class BusinessDetailSerializer(BusinessSerializer):
    """
    Serializer for detailed business information (detail view)
    """
    reviews = BusinessReviewSerializer(many=True, read_only=True)
    
    class Meta(BusinessSerializer.Meta):
        fields = BusinessSerializer.Meta.fields + ['reviews'] 