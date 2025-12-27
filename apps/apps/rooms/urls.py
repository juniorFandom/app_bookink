from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import web as views
from .views import api
from .views.web import finalize_payment, finalize_payment_admin, process_cash_payment, cancel_booking, approve_booking

app_name = 'rooms'

# API Router
router = DefaultRouter()
router.register(r'api/room-types', api.RoomTypeViewSet, basename='room-type')
router.register(r'api/rooms', api.RoomViewSet, basename='room')
router.register(r'api/bookings', api.RoomBookingViewSet, basename='booking')

urlpatterns = [
    # Web URLs
    # General room listing (for navigation)
    path(
        '',
        views.general_room_list,
        name='general_room_list'
    ),
    # Advanced room search
    path(
        'search/',
        views.room_search,
        name='room_search'
    ),
    # Business-specific room listing
    path(
        'business/<int:business_location_id>/rooms/',
        views.room_list,
        name='room_list'
    ),
    # Room management URLs
    path(
        'business/<int:business_location_id>/rooms/create/',
        views.room_create,
        name='room_create'
    ),
    path(
        '<int:pk>/edit/',
        views.room_edit,
        name='room_edit'
    ),
    path(
        '<int:pk>/',
        views.room_detail,
        name='room_detail'
    ),
    path(
        '<int:room_id>/book/',
        views.room_booking_create,
        name='book'
    ),
    path(
        'bookings/<str:reference>/',
        views.booking_detail,
        name='booking_detail'
    ),
    
    # Image upload AJAX endpoint (pour chambres existantes)
    path(
        '<int:room_id>/upload-image/',
        views.upload_room_image,
        name='upload_room_image'
    ),
    path(
        '<int:room_id>/delete-image/<int:image_id>/',
        views.delete_room_image,
        name='delete_room_image'
    ),
    path(
        '<int:room_id>/reorder-images/',
        views.reorder_room_images,
        name='reorder_room_images'
    ),
    
    # Image upload temporaire (pour nouvelles chambres)
    path(
        'upload-image-temp/',
        views.upload_image_temp,
        name='upload_image_temp'
    ),
    path(
        'delete-image-temp/<int:image_id>/',
        views.delete_image_temp,
        name='delete_image_temp'
    ),
    path(
        'list-image-temp/',
        views.list_image_temp,
        name='list_image_temp'
    ),
    
    # Liste des types de chambres pour une business location
    path(
        'business/<int:business_location_id>/room-types/',
        views.room_type_list,
        name='room_type_list'
    ),
    # Liste des réservations pour une business location
    path(
        'business/<int:business_location_id>/bookings/',
        views.booking_list,
        name='booking_list'
    ),
    
    # API URLs
    path('', include(router.urls)),
    path('booking/<str:reference>/finalize-payment/', finalize_payment, name='finalize_payment'),
    path('booking/<str:reference>/finalize-payment-admin/', finalize_payment_admin, name='finalize_payment_admin'),
    path('booking/<str:reference>/process-cash-payment/', process_cash_payment, name='process_cash_payment'),
    path('booking/<str:reference>/approve/', approve_booking, name='approve_booking'),
    path('booking/<str:reference>/cancel/', cancel_booking, name='cancel_booking'),
] 