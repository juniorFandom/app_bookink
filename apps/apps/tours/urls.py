from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.api import (
    TourViewSet, TourDestinationViewSet,
    TourDestinationImageViewSet, TourBookingViewSet,
    TourScheduleViewSet, TourReviewViewSet
)
from .views import web

# API Router
router = DefaultRouter()
router.register(r'tours', TourViewSet, basename='tour')
# router.register(r'tours/(?P<tour_slug>[^/.]+)/images', TourImageViewSet, basename='tour-image')  # supprimé car le modèle n'existe plus
router.register(r'tours/(?P<tour_slug>[^/.]+)/destinations', TourDestinationViewSet, basename='tour-destination')
router.register(r'tours/(?P<tour_slug>[^/.]+)/destinations/(?P<destination_slug>[^/.]+)/images', TourDestinationImageViewSet, basename='tour-destination-image')
router.register(r'tours/(?P<tour_slug>[^/.]+)/bookings', TourBookingViewSet, basename='tour-booking')
router.register(r'tours/(?P<tour_slug>[^/.]+)/schedules', TourScheduleViewSet, basename='tour-schedule')
router.register(r'tours/(?P<tour_slug>[^/.]+)/reviews', TourReviewViewSet, basename='tour-review')

app_name = 'tours'

urlpatterns = [
    # API Routes
    path('api/', include(router.urls)),
    
    # Web Routes - Tours
    path('', web.tour_list, name='tour_list'),
    path('search/', web.tour_list, name='tour_search'),
    path('create/', web.tour_create, name='tour_create'),
    path('itineraries/', web.itinerary_list, name='itinerary_list'),
    
    # Web Routes - Destinations (avant le pattern générique)
    path('destinations/create/', web.destination_create, name='destination_create'),
    path('destinations/select/', web.destination_select, name='destination_select'),
    path('destinations/<slug:slug>/edit/', web.destination_edit, name='destination_edit'),
    path('destinations/<slug:slug>/', web.destination_detail, name='destination_detail'),
    path('destinations/', web.destination_list, name='destination_list'),
    
    # Web Routes - Activities (avant le pattern générique)
    path('activities/create/', web.activity_create, name='activity_create'),
    path('activities/<slug:slug>/edit/', web.activity_edit, name='activity_edit'),
    path('activities/<slug:slug>/delete/', web.activity_delete, name='activity_delete'),
    path('activities/<slug:slug>/', web.activity_detail, name='activity_detail'),
    path('activities/', web.activity_list, name='activity_list'),
    path('activities/select/', web.activity_select, name='activity_select'),
    
    # Web Routes - Bookings
    path('bookings/', web.tour_booking_list, name='booking_list'),
    path('bookings/<int:pk>/', web.tour_booking_detail, name='booking_detail'),
    path('bookings/<int:pk>/payment/', web.tour_booking_payment, name='booking_payment'),
    
    # Tour detail (pattern générique en dernier)
    path('<slug:slug>/', web.tour_detail, name='tour_detail'),
    path('<slug:slug>/edit/', web.tour_edit, name='tour_edit'),
    path('<slug:slug>/images/upload/', web.tour_image_upload, name='tour_image_upload'),
    path('<slug:slug>/book/', web.tour_booking_create, name='tour_booking_create'),
    path('<slug:slug>/review/', web.tour_review_create, name='tour_review_create'),
    path('<slug:slug>/inquiry/', web.tour_inquiry, name='tour_inquiry'),
]