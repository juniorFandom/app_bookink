from django.urls import path
from . import views
from .views.web import add_to_cart, cart_detail, cart_clear, cart_update_quantity, cart_remove_item, valider_commande, validate_order

app_name = 'orders'

urlpatterns = [
    # Food Categories
    path('categories/', views.food_category_list, name='food_category_list'),
    path('categories/create/', views.food_category_create, name='food_category_create'),
    path('categories/<int:pk>/', views.food_category_detail, name='food_category_detail'),
    path('categories/<int:pk>/edit/', views.food_category_edit, name='food_category_edit'),
    path('categories/<int:pk>/delete/', views.food_category_delete, name='food_category_delete'),

    # Menu Items
    path('menu-items/', views.menu_item_list, name='menu_item_list'),
    path('menu-items/create/', views.menu_item_create, name='menu_item_create'),
    path('menu-items/<int:pk>/', views.menu_item_detail, name='menu_item_detail'),
    path('menu-items/<int:pk>/edit/', views.menu_item_edit, name='menu_item_edit'),
    path('menu-items/<int:pk>/delete/', views.menu_item_delete, name='menu_item_delete'),
    path('menu-items/<int:pk>/images/', views.menu_item_images, name='menu_item_images'),
    path('menu-items/<int:pk>/images/add/', views.menu_item_image_add, name='menu_item_image_add'),
    path('menu-items/<int:pk>/images/<int:image_id>/delete/', views.menu_item_image_delete, name='menu_item_image_delete'),
    path('menu-item/<int:pk>/add-to-cart/', add_to_cart, name='add_to_cart'),

    path('cart/', cart_detail, name='cart_detail'),
    path('cart/clear/', cart_clear, name='cart_clear'),
    path('cart/update/<int:pk>/', cart_update_quantity, name='cart_update_quantity'),
    path('cart/remove/<int:pk>/', cart_remove_item, name='cart_remove_item'),
    path('cart/valider/', valider_commande, name='valider_commande'),

    # Orders
    path('', views.order_list, name='order_list'),
    path('create/', views.order_create, name='order_create'),
    path('<str:order_number>/', views.order_detail, name='order_detail'),
    path('<str:order_number>/edit/', views.order_edit, name='order_edit'),
    path('<str:order_number>/cancel/', views.order_cancel, name='order_cancel'),
    path('<str:order_number>/status/', views.order_status_update, name='order_status_update'),
    path('<str:order_number>/payment/', views.order_payment_update, name='order_payment_update'),
    path('<str:order_number>/items/add/', views.order_item_add, name='order_item_add'),
    path('<str:order_number>/items/<int:item_id>/edit/', views.order_item_edit, name='order_item_edit'),
    path('<str:order_number>/items/<int:item_id>/delete/', views.order_item_delete, name='order_item_delete'),
    path('<str:order_number>/validate/', validate_order, name='validate_order'),

    # API endpoints for AJAX requests
    path('api/menu-items/', views.api_menu_items, name='api_menu_items'),
    path('api/order-items/', views.api_order_items, name='api_order_items'),
    path('api/order-total/', views.api_order_total, name='api_order_total'),
] 