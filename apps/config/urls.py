from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from apps.business.views.web import debug_businesses

urlpatterns = [
    # Page d'accueil à la racine
    path('', include('apps.home.urls')),

    # Administration
    path('admin/', admin.site.urls),


    # Modules applicatifs
    path('users/', include('apps.users.urls')),        # Inscription, connexion, profils
    path('guides/', include('apps.guides.urls')),      # Gestion des guides
    path('business/', include('apps.business.urls')),  # Profils entreprises, adresses
    path('tours/', include('apps.tours.urls')),        # Packages, galeries, calendriers
    path('rooms/', include('apps.rooms.urls')),  # Hébergements et chambres
    path('vehicles/', include('apps.vehicles.urls')),  # Location de véhicules
    path('orders/', include('apps.orders.urls')),      # Commandes restaurants, historique
    path('wallets/', include('apps.wallets.urls')),    # Wallet & transactions
    path('tourist-sites/', include('apps.tourist_sites.urls')),  # Sites touristiques
    
    # Debug endpoint temporaire
    path('debug-businesses/', debug_businesses, name='debug_businesses'),

    # API REST (DRF)
    path('api-auth/', include('rest_framework.urls')),
]

# Servir les fichiers média et statiques en mode debug
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
