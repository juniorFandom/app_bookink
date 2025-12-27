from django.urls import path
from . import business, location, review

app_name = 'admin'

# Business URLs
urlpatterns = [
    path('', business.business_dashboard, name='dashboard'),
    # Dashboard
    path('dashboard/', business.business_dashboard, name='dashboard'),
    
    # Business management
    path('list/', business.business_list, name='business_list'),
    path('create/', business.business_create, name='business_create'),
    path('<int:pk>/', business.business_detail, name='business_detail'),
    path('<int:pk>/edit/', business.business_edit, name='business_edit'),
    path('<int:pk>/delete/', business.business_delete, name='business_delete'),
    path('<int:pk>/toggle-status/', business.business_toggle_status, name='business_toggle_status'),
    path('<int:pk>/toggle-verification/', business.business_toggle_verification, name='business_toggle_verification'),
    
    # Location management
    path('location/dashboard/', location.location_dashboard, name='location_dashboard'),
    path('location/', location.location_list, name='location_list'),
    path('location/create/', location.location_create, name='location_create'),
    path('location/<int:pk>/', location.location_detail, name='location_detail'),
    path('location/<int:pk>/edit/', location.location_edit, name='location_edit'),
    path('location/<int:pk>/delete/', location.location_delete, name='location_delete'),
    path('location/<int:pk>/toggle-status/', location.location_toggle_status, name='location_toggle_status'),
    path('location/<int:pk>/toggle-verification/', location.location_toggle_verification, name='location_toggle_verification'),
    path('location/<int:pk>/toggle-featured/', location.location_toggle_featured, name='location_toggle_featured'),
    path('location/<int:pk>/image/<int:image_id>/delete/', location.location_image_delete, name='location_image_delete'),
    path('location/<int:pk>/image/<int:image_id>/primary/', location.location_image_primary, name='location_image_primary'),
    
    # Review management
    path('review/dashboard/', review.review_dashboard, name='review_dashboard'),
    path('review/', review.review_list, name='review_list'),
    path('review/<int:pk>/', review.review_detail, name='review_detail'),
    path('review/<int:pk>/edit/', review.review_edit, name='review_edit'),
    path('review/<int:pk>/delete/', review.review_delete, name='review_delete'),
    path('review/<int:pk>/approve/', review.review_approve, name='review_approve'),
    path('review/<int:pk>/reject/', review.review_reject, name='review_reject'),
    path('review/analytics/', review.review_analytics, name='review_analytics'),
] 