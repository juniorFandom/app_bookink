"""Guide app API views."""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from ..models import GuideProfile
from ..serializers import (
    GuideProfileSerializer,
    GuideProfileCreateSerializer,
    GuideProfileUpdateSerializer,
    GuideVerificationSerializer
)
from ..services import (
    create_guide_profile,
    update_guide_profile,
    verify_guide_profile,
    get_guide_profile,
    get_verified_guides
)


class GuideProfileListAPIView(generics.ListAPIView):
    """API view for listing guide profiles."""
    queryset = GuideProfile.objects.filter(is_verified=True)
    serializer_class = GuideProfileSerializer
    permission_classes = [permissions.AllowAny]


class GuideProfileCreateAPIView(generics.CreateAPIView):
    """API view for creating guide profiles."""
    serializer_class = GuideProfileCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Create guide profile for the current user."""
        create_guide_profile(
            user=self.request.user,
            **serializer.validated_data
        )


class GuideProfileDetailAPIView(generics.RetrieveAPIView):
    """API view for retrieving guide profile details."""
    queryset = GuideProfile.objects.all()
    serializer_class = GuideProfileSerializer
    permission_classes = [permissions.AllowAny]


class GuideProfileUpdateAPIView(generics.UpdateAPIView):
    """API view for updating guide profiles."""
    serializer_class = GuideProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Get the current user's guide profile."""
        return get_object_or_404(GuideProfile, user=self.request.user)

    def perform_update(self, serializer):
        """Update guide profile."""
        profile = self.get_object()
        update_guide_profile(profile, serializer.validated_data)


class GuideProfileVerificationAPIView(generics.UpdateAPIView):
    """API view for uploading verification documents."""
    serializer_class = GuideVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Get the current user's guide profile."""
        return get_object_or_404(GuideProfile, user=self.request.user)

    def perform_update(self, serializer):
        """Update verification document."""
        profile = self.get_object()
        profile.verification_document = serializer.validated_data['verification_document']
        profile.save()


class GuideProfileMyAPIView(generics.RetrieveAPIView):
    """API view for retrieving current user's guide profile."""
    serializer_class = GuideProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Get the current user's guide profile."""
        return get_object_or_404(GuideProfile, user=self.request.user) 