from django import template
from django.urls import reverse, NoReverseMatch
from django.conf import settings
import importlib
import re

register = template.Library()

@register.inclusion_tag('core/navigation_menu.html')
def navigation_menu():
    """
    Génère un menu de navigation basé sur toutes les routes disponibles
    dans les applications Django.
    """
    menu_items = []
    
    # Configuration des applications et leurs préfixes
    app_configs = {
        'home': {'prefix': '', 'title': 'Accueil', 'icon': 'fas fa-home'},
        'users': {'prefix': 'users/', 'title': 'Utilisateurs', 'icon': 'fas fa-users'},
        'guides': {'prefix': 'guides/', 'title': 'Guides', 'icon': 'fas fa-user-tie'},
        'business': {'prefix': 'business/', 'title': 'Entreprises', 'icon': 'fas fa-building'},
        'tours': {'prefix': 'tours/', 'title': 'Tours', 'icon': 'fas fa-map-marked-alt'},
        'rooms': {'prefix': 'rooms/', 'title': 'Hébergements', 'icon': 'fas fa-bed'},
        'vehicles': {'prefix': 'vehicles/', 'title': 'Véhicules', 'icon': 'fas fa-car'},
        'orders': {'prefix': 'orders/', 'title': 'Commandes', 'icon': 'fas fa-shopping-cart'},
        'wallets': {'prefix': 'wallets/', 'title': 'Portefeuilles', 'icon': 'fas fa-wallet'},
        'tourist_sites': {'prefix': 'tourist-sites/', 'title': 'Sites Touristiques', 'icon': 'fas fa-map-marker-alt'},
    }
    
    def has_parameters(pattern_route):
        """Vérifie si une route contient des paramètres"""
        return bool(re.search(r'<[^>]+>', pattern_route))
    
    def get_icon_for_route(route_name):
        """Retourne une icône appropriée basée sur le nom de la route"""
        route_lower = route_name.lower()
        if 'create' in route_lower or 'add' in route_lower:
            return 'fas fa-plus'
        elif 'edit' in route_lower or 'update' in route_lower:
            return 'fas fa-edit'
        elif 'delete' in route_lower or 'remove' in route_lower:
            return 'fas fa-trash'
        elif 'detail' in route_lower or 'view' in route_lower:
            return 'fas fa-eye'
        elif 'list' in route_lower:
            return 'fas fa-list'
        elif 'login' in route_lower:
            return 'fas fa-sign-in-alt'
        elif 'logout' in route_lower:
            return 'fas fa-sign-out-alt'
        elif 'register' in route_lower:
            return 'fas fa-user-plus'
        elif 'profile' in route_lower:
            return 'fas fa-id-card'
        elif 'password' in route_lower:
            return 'fas fa-key'
        elif 'booking' in route_lower:
            return 'fas fa-calendar-check'
        elif 'review' in route_lower:
            return 'fas fa-star'
        elif 'image' in route_lower:
            return 'fas fa-image'
        elif 'payment' in route_lower:
            return 'fas fa-credit-card'
        elif 'transaction' in route_lower:
            return 'fas fa-exchange-alt'
        elif 'deposit' in route_lower:
            return 'fas fa-arrow-down'
        elif 'withdraw' in route_lower:
            return 'fas fa-arrow-up'
        elif 'transfer' in route_lower:
            return 'fas fa-exchange-alt'
        else:
            return 'fas fa-link'
    
    for app_name, config in app_configs.items():
        try:
            # Import dynamique du module urls de l'application
            urls_module = importlib.import_module(f'apps.{app_name}.urls')
            
            app_items = []
            app_name_attr = getattr(urls_module, 'app_name', app_name)
            
            # Parcourir les patterns d'URL
            for pattern in urls_module.urlpatterns:
                if hasattr(pattern, 'name') and pattern.name:
                    # Ignorer les routes API
                    pattern_route = getattr(pattern.pattern, '_route', '')
                    if 'api' not in pattern_route and not has_parameters(pattern_route):
                        try:
                            # Construire le nom complet de la route
                            full_name = f"{app_name_attr}:{pattern.name}"
                            url = reverse(full_name)
                            
                            # Créer un nom d'affichage lisible
                            display_name = pattern.name.replace('_', ' ').replace('-', ' ').title()
                            
                            # Obtenir l'icône appropriée
                            icon = get_icon_for_route(pattern.name)
                            
                            app_items.append({
                                'name': display_name,
                                'url': url,
                                'full_name': full_name,
                                'pattern': pattern_route,
                                'icon': icon
                            })
                        except NoReverseMatch:
                            # Ignorer les routes qui nécessitent des paramètres
                            continue
            
            # Trier les éléments par nom
            app_items.sort(key=lambda x: x['name'])
            
            if app_items:
                menu_items.append({
                    'app_title': config['title'],
                    'app_name': app_name,
                    'app_icon': config['icon'],
                    'items': app_items
                })
                
        except (ImportError, AttributeError):
            # Ignorer les applications qui n'ont pas de module urls
            continue
    
    return {'menu_items': menu_items} 