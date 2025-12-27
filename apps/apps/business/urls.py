from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views.web import business_location_wallet_api, create_restaurant_order_from_dashboard

app_name = 'business'

# API Router
router = DefaultRouter()
router.register(r'businesses', views.api.BusinessViewSet)
router.register(r'locations', views.api.BusinessLocationViewSet)
router.register(r'reviews', views.api.BusinessReviewViewSet, basename='review')
router.register(r'amenity-categories', views.api.BusinessAmenityCategoryViewSet)
router.register(r'amenities', views.api.BusinessAmenityViewSet)

# Web URL patterns
web_urlpatterns = [
    # Business views
    path('', views.web.business_list, name='business_list'),
    path('my-businesses/', views.web.my_businesses, name='my_businesses'),
    path('<int:pk>/', views.web.business_detail, name='business_detail'),
    path('create/', views.web.business_create, name='business_create'),
    path('<int:pk>/edit/', views.web.business_edit, name='business_edit'),
    
    # Financial dashboard
    path('financial-dashboard/', views.web.financial_dashboard, name='financial_dashboard'),
    
    # Location views
    path('<int:business_pk>/location/create/', views.web.business_location_wizard, name='location_create'),
    path('location/<int:pk>/edit/', views.web.business_location_wizard, name='location_edit'),
    path('location/<int:location_pk>/images/', views.web.location_image_upload, name='location_images'),
    path('location/<int:location_pk>/hours/', views.web.location_hours_edit, name='location_hours'),
    path('location/<int:pk>/', views.web.location_detail, name='location_detail'),
    path('location/<int:pk>/dashboard/', views.web.business_location_dashboard, name='business_location_dashboard'),
    
    # Permission management
    path('location/<int:location_pk>/permissions/', views.permissions.permission_list, name='permission_list'),
    path('location/<int:location_pk>/permissions/create/', views.permissions.permission_create, name='permission_create'),
    path('permission/<int:permission_pk>/edit/', views.permissions.permission_edit, name='permission_edit'),
    path('permission/<int:permission_pk>/delete/', views.permissions.permission_delete, name='permission_delete'),
    path('location/<int:location_pk>/permissions/search-users/', views.permissions.user_search, name='user_search'),
    path('permissions/requests/', views.permissions.permission_request_list, name='permission_request_list'),
    path('permissions/requests/<int:request_pk>/', views.permissions.permission_request_detail, name='permission_request_detail'),
    path('permissions/my-permissions/', views.permissions.my_permissions, name='my_permissions'),
    path('permissions/request/', views.permissions.request_permission, name='request_permission'),
    
    # Interface d'administration des accès
    path('permissions/access-management/', views.permissions.access_management, name='access_management'),
    path('permissions/location/<int:location_pk>/manage-access/', views.permissions.manage_location_access, name='manage_location_access'),
    path('permissions/location/<int:location_pk>/quick-grant/', views.permissions.quick_grant_permission, name='quick_grant_permission'),
    path('permissions/<int:permission_pk>/quick-revoke/', views.permissions.quick_revoke_permission, name='quick_revoke_permission'),
    
    # Logs d'actions
    path('permissions/action-logs/', views.permissions.action_logs, name='action_logs'),
    path('permissions/location/<int:location_pk>/action-logs/', views.permissions.action_logs, name='location_action_logs'),
    
    # Review views
    path('<int:pk>/review/', views.web.add_review, name='add_review'),
    
    # Wizard views
    path('location/wizard/create/<int:business_pk>/', views.web.business_location_wizard, name='location_wizard_create'),
    path('location/wizard/edit/<int:pk>/', views.web.business_location_wizard, name='location_wizard_edit'),
    path('location/wizard/reset/<int:business_pk>/', views.web.reset_wizard, name='location_wizard_reset'),
    
    # AJAX endpoints for wizard image upload
    path('location/upload-image-temp/', views.web.upload_image_temp, name='upload_image_temp'),
    path('location/delete-image-temp/<int:image_id>/', views.web.delete_image_temp, name='delete_image_temp'),
    path('location/list-image-temp/', views.web.list_image_temp, name='list_image_temp'),
    path('location/<int:pk>/wallet-api/', business_location_wallet_api, name='business_location_wallet_api'),
    path('location/finalize-wallet-transaction/', views.web.finalize_wallet_transaction, name='finalize_wallet_transaction'),
    path('location/<int:pk>/order/create/', create_restaurant_order_from_dashboard, name='create_restaurant_order_from_dashboard'),
    
    # Debug endpoint
    path('debug-businesses/', views.web.debug_businesses, name='debug_businesses'),
]

# Admin URL patterns
admin_urlpatterns = [
    path('admin/', include('apps.business.views.admin.urls')),
    path('super-admin/', include('apps.business.views.admin.super_admin_urls')),
]

# API URL patterns
api_urlpatterns = [ 
    path('api/', include(router.urls)),
]

# Combined URL patterns
urlpatterns = web_urlpatterns + admin_urlpatterns + api_urlpatterns 