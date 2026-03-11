"""Guide app views."""
from .web import (
    GuideProfileCreateView,
    GuideProfileUpdateView,
    GuideProfileDetailView,
    GuideProfileListView
)
from .api import (
    GuideProfileListAPIView,
    GuideProfileCreateAPIView,
    GuideProfileDetailAPIView,
    GuideProfileUpdateAPIView,
    GuideProfileVerificationAPIView,
    GuideProfileMyAPIView
)


__all__ = [
    # Web views
    'GuideProfileCreateView',
    'GuideProfileUpdateView',
    'GuideProfileDetailView',
    'GuideProfileListView',
    # API views
    'GuideProfileListAPIView',
    'GuideProfileCreateAPIView',
    'GuideProfileDetailAPIView',
    'GuideProfileUpdateAPIView',
    'GuideProfileVerificationAPIView',
    'GuideProfileMyAPIView'
]
