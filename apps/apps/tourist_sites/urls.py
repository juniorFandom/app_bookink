from django.urls import path
from apps.tourist_sites.views import views

app_name = 'tourist_sites'

urlpatterns = [
    # Vues publiques
    path('', views.tourist_sites_list, name='sites_list'),
    path('map/', views.tourist_sites_map, name='sites_map'),
    path('api/', views.tourist_sites_api, name='sites_api'),
    path('<int:site_id>/', views.tourist_site_detail, name='site_detail'),
    
    # Vues Super Admin
    path('admin/dashboard/', views.super_admin_sites_dashboard, name='super_admin_dashboard'),
    path('admin/sites/', views.super_admin_sites_list, name='super_admin_sites_list'),
    path('admin/sites/<int:site_id>/', views.super_admin_site_detail, name='super_admin_site_detail'),
    path('admin/sites/<int:site_id>/delete/', views.super_admin_site_delete, name='super_admin_site_delete'),
    path('admin/sites/create/', views.super_admin_site_create, name='super_admin_site_create'),
    path('admin/categories/', views.super_admin_categories_list, name='super_admin_categories_list'),
    path('admin/categories/<int:category_id>/delete/', views.super_admin_category_delete, name='super_admin_category_delete'),
    path('admin/sites/<int:site_id>/api/', views.super_admin_site_detail_api, name='super_admin_site_detail_api'),
    path('admin/sites/<int:site_id>/edit/', views.super_admin_site_edit, name='super_admin_site_edit'),
    path('admin/categories/<int:category_id>/api/', views.super_admin_category_detail_api, name='super_admin_category_detail_api'),
    path('admin/categories/<int:category_id>/edit/', views.super_admin_category_edit, name='super_admin_category_edit'),
    
    # Zones Dangereuses
    path('admin/zones_dangereuses/', views.super_admin_zones_dangereuses_list, name='super_admin_zones_dangereuses_list'),
    path('admin/zones_dangereuses/create/', views.super_admin_zones_dangereuses_create, name='super_admin_zones_dangereuses_create'),
    path('admin/zones_dangereuses/<int:zone_id>/', views.zone_dangereuse_detail, name='zone_dangereuse_detail'),
    path('admin/zones_dangereuses/<int:zone_id>/edit/', views.zone_dangereuse_edit, name='zone_dangereuse_edit'),
    path('admin/zones_dangereuses/<int:zone_id>/delete/', views.zone_dangereuse_delete, name='zone_dangereuse_delete'),
    path('admin/zones_dangereuses/<int:zone_id>/validate/', views.zone_dangereuse_validate, name='zone_dangereuse_validate'),
    path('admin/zones_dangereuses/<int:zone_id>/resolve/', views.zone_dangereuse_resolve, name='zone_dangereuse_resolve'),
    path('admin/zones_dangereuses/<int:zone_id>/api/', views.zone_dangereuse_detail_api, name='zone_dangereuse_detail_api'),
    path('api/zones/signalement/', views.signaler_zone_dangereuse, name='signaler_zone_dangereuse'),
    path('api/zones/<int:zone_id>/vote/', views.vote_zone_dangereuse, name='vote_zone_dangereuse'),
] 