"""Guide app serializers."""
from rest_framework import serializers

from apps.users.serializers import UserSerializer
from .models import GuideProfile


class GuideProfileSerializer(serializers.ModelSerializer):
    """Serializer for guide profiles."""
    user = UserSerializer(read_only=True)

    class Meta:
        model = GuideProfile
        fields = [
            'id',
            'user',
            'business_location',
            'license_number',
            'years_of_experience',
            'languages_spoken',
            'specializations',
            'hourly_rate',
            'is_verified',
            'verification_document',
            'bio',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GuideProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating guide profiles."""
    
    class Meta:
        model = GuideProfile
        fields = [
            'business_location',
            'license_number',
            'years_of_experience',
            'languages_spoken',
            'specializations',
            'hourly_rate',
            'bio'
        ]


class GuideProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating guide profiles."""
    
    class Meta:
        model = GuideProfile
        fields = [
            'business_location',
            'license_number',
            'years_of_experience',
            'languages_spoken',
            'specializations',
            'hourly_rate',
            'bio'
        ]


class GuideVerificationSerializer(serializers.ModelSerializer):
    """Serializer for guide verification document upload."""
    
    class Meta:
        model = GuideProfile
        fields = ['verification_document'] 