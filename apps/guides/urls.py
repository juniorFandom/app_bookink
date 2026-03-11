"""Guide app URL configuration."""
from django.urls import path

from .views.web import (
    GuideProfileCreateView,
    GuideProfileUpdateView,
    GuideProfileDetailView,
    GuideProfileListView
)

app_name = 'guides'

urlpatterns = [
    # Guide Profile URLs
    path('profile/create/', GuideProfileCreateView.as_view(), name='profile_create'),
    path('profile/edit/', GuideProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/', GuideProfileDetailView.as_view(), name='profile_detail'),
    path('profile/<int:pk>/', GuideProfileDetailView.as_view(), name='profile_detail_by_id'),
    path('profiles/', GuideProfileListView.as_view(), name='profile_list'),
] 