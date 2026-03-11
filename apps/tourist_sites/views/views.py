from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from apps.tourist_sites.models import TouristSite, TouristSiteCategory, TouristSiteImage, ZoneDangereuse, ZoneDangereuseVote
from math import radians, cos, sin, asin, sqrt
from django.views.decorators.http import require_POST
from apps.tourist_sites.models import Notification
from django.views.decorators.csrf import csrf_exempt
import json
from django.urls import reverse


def tourist_sites_list(request):
    """Vue pour afficher la liste des sites touristiques"""
    sites = TouristSite.objects.filter(is_active=True).select_related('category')
    categories = TouristSiteCategory.objects.all()
    
    # Filtres
    category_id = request.GET.get('category')
    if category_id:
        sites = sites.filter(category_id=category_id)
    
    context = {
        'sites': sites,
        'categories': categories,
        'selected_category': category_id,
    }
    return render(request, 'tourist_sites/sites_list.html', context)


def tourist_site_detail(request, site_id):
    """Vue pour afficher les détails d'un site touristique"""
    site = get_object_or_404(TouristSite, id=site_id, is_active=True)
    context = {
        'site': site,
    }
    return render(request, 'tourist_sites/site_detail.html', context)


def tourist_sites_map(request):
    """Vue pour afficher la carte des sites touristiques"""
    sites = TouristSite.objects.filter(is_active=True).select_related('category')
    context = {
        'sites': sites,
    }
    return render(request, 'tourist_sites/sites_map.html', context)


@login_required
def tourist_sites_api(request):
    """API pour récupérer les sites touristiques en JSON (pour la carte)"""
    from apps.business.models import BusinessLocation
    from math import radians, cos, sin, asin, sqrt
    
    def haversine(lat1, lon1, lat2, lon2):
        """Calcule la distance entre deux points géographiques en km"""
        R = 6371  # Rayon de la Terre en km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return R * c
    
    sites = TouristSite.objects.filter(is_active=True).select_related('category')
    
    sites_data = []
    for site in sites:
        # Trouver les business locations à proximité (dans un rayon de 10km)
        nearby_businesses = []
        business_locations = BusinessLocation.objects.filter(
            is_active=True,
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        for business_loc in business_locations:
            distance = haversine(
                float(site.latitude), float(site.longitude),
                float(business_loc.latitude), float(business_loc.longitude)
            )
            
            # Si la business location est à moins de 10km du site
            if distance <= 10:
                nearby_businesses.append({
                    'id': business_loc.id,
                    'name': business_loc.name,
                    'type': business_loc.get_business_location_type_display(),
                    'distance': round(distance, 1),
                    'business_id': business_loc.business.id if business_loc.business else None,
                    'business_name': business_loc.business.name if business_loc.business else '',
                    'url': f'/business/location/{business_loc.id}/'
                })
        
        # Trier par distance et prendre les 3 plus proches
        nearby_businesses.sort(key=lambda x: x['distance'])
        nearby_businesses = nearby_businesses[:3]
        
        site_data = {
            'id': site.id,
            'name': site.name,
            'description': site.description,
            'latitude': float(site.latitude),
            'longitude': float(site.longitude),
            'category': site.category.name if site.category else None,
            'nearby_businesses': nearby_businesses,
        }
        sites_data.append(site_data)
    
    return JsonResponse({'sites': sites_data})


# Vues Super Admin
def is_super_admin(user):
    """Vérifie si l'utilisateur est un super admin"""
    return user.is_authenticated and user.is_superuser


@login_required
@user_passes_test(is_super_admin)
def super_admin_sites_dashboard(request):
    """Dashboard super admin pour la gestion des sites touristiques"""
    # Statistiques des sites
    total_sites = TouristSite.objects.count()
    active_sites = TouristSite.objects.filter(is_active=True).count()
    total_categories = TouristSiteCategory.objects.count()
    recent_sites = TouristSite.objects.order_by('-created_at')[:5]
    
    # Statistiques des zones dangereuses
    total_zones = ZoneDangereuse.objects.count()
    zones_signalees = ZoneDangereuse.objects.filter(statut=ZoneDangereuse.Statut.SIGNALEE).count()
    zones_verifiees = ZoneDangereuse.objects.filter(statut=ZoneDangereuse.Statut.VERIFIEE).count()
    zones_resolues = ZoneDangereuse.objects.filter(statut=ZoneDangereuse.Statut.RESOLUE).count()
    recent_zones = ZoneDangereuse.objects.order_by('-date_signalement')[:5]
    
    # Sites par catégorie
    sites_by_category = []
    for category in TouristSiteCategory.objects.all():
        count = TouristSite.objects.filter(category=category).count()
        sites_by_category.append({
            'category': category.name,
            'count': count
        })
    
    # Données pour les filtres
    categories = TouristSiteCategory.objects.all()
    
    # Filtres pour la liste des sites
    sites = TouristSite.objects.all().select_related('category').order_by('-created_at')
    category_id = request.GET.get('category')
    search = request.GET.get('search')
    status = request.GET.get('status')
    
    if category_id:
        sites = sites.filter(category_id=category_id)
    
    if search:
        sites = sites.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    if status:
        if status == 'active':
            sites = sites.filter(is_active=True)
        elif status == 'inactive':
            sites = sites.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(sites, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'total_sites': total_sites,
        'active_sites': active_sites,
        'total_categories': total_categories,
        'recent_sites': recent_sites,
        'total_zones': total_zones,
        'zones_signalees': zones_signalees,
        'zones_verifiees': zones_verifiees,
        'zones_resolues': zones_resolues,
        'recent_zones': recent_zones,
        'sites_by_category': sites_by_category,
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_id,
        'search': search,
        'status': status,
    }
    return render(request, 'tourist_sites/admin/super_admin_sites_dashboard.html', context)


@login_required
@user_passes_test(is_super_admin)
def super_admin_sites_list(request):
    """Liste des sites touristiques pour le super admin"""
    sites = TouristSite.objects.all().select_related('category').order_by('-created_at')
    categories = TouristSiteCategory.objects.all()
    
    # Filtres
    category_id = request.GET.get('category')
    search = request.GET.get('search')
    status = request.GET.get('status')
    
    if category_id:
        sites = sites.filter(category_id=category_id)
    
    if search:
        sites = sites.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    if status:
        if status == 'active':
            sites = sites.filter(is_active=True)
        elif status == 'inactive':
            sites = sites.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(sites, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_id,
        'search': search,
        'status': status,
    }
    return render(request, 'tourist_sites/admin/super_admin_sites_list.html', context)


@login_required
@user_passes_test(is_super_admin)
def super_admin_site_detail(request, site_id):
    """Détails d'un site touristique pour le super admin"""
    site = get_object_or_404(TouristSite, id=site_id)
    
    if request.method == 'POST':
        # Toggle du statut actif/inactif
        if 'toggle_status' in request.POST:
            site.is_active = not site.is_active
            site.save()
            messages.success(request, f'Le statut du site "{site.name}" a été modifié.')
            return redirect('tourist_sites:super_admin_site_detail', site_id=site.id)
    
    context = {
        'site': site,
    }
    return render(request, 'tourist_sites/admin/super_admin_site_detail.html', context)


@login_required
@user_passes_test(is_super_admin)
def super_admin_site_detail_api(request, site_id):
    """API JSON pour le détail d'un site touristique (modale édition)"""
    try:
        site = TouristSite.objects.get(id=site_id)
        data = {
            'id': site.id,
            'name': site.name,
            'category_id': site.category.id if site.category else None,
            'description': site.description,
            'latitude': float(site.latitude),
            'longitude': float(site.longitude),
            'is_active': site.is_active,
        }
        return JsonResponse({'success': True, 'site': data})
    except TouristSite.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Site non trouvé.'})


@login_required
@user_passes_test(is_super_admin)
def super_admin_categories_list(request):
    """Liste des catégories pour le super admin"""
    categories = TouristSiteCategory.objects.all().order_by('name')
    
    if request.method == 'POST':
        # Ajouter une nouvelle catégorie
        if 'add_category' in request.POST:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            
            if name:
                category, created = TouristSiteCategory.objects.get_or_create(
                    name=name,
                    defaults={'description': description}
                )
                if created:
                    messages.success(request, f'Catégorie "{name}" créée avec succès.')
                else:
                    messages.warning(request, f'La catégorie "{name}" existe déjà.')
                return redirect('tourist_sites:super_admin_categories_list')
    
    context = {
        'categories': categories,
    }
    return render(request, 'tourist_sites/admin/super_admin_categories_list.html', context)


@login_required
@user_passes_test(is_super_admin)
def super_admin_site_delete(request, site_id):
    """Supprimer un site touristique"""
    if request.method == 'POST':
        try:
            site = TouristSite.objects.get(id=site_id)
            site_name = site.name
            site.delete()
            return JsonResponse({'success': True, 'message': f'Site "{site_name}" supprimé avec succès.'})
        except TouristSite.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Site non trouvé.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'})


@login_required
@user_passes_test(is_super_admin)
def super_admin_category_delete(request, category_id):
    """Supprimer une catégorie"""
    if request.method == 'POST':
        try:
            category = TouristSiteCategory.objects.get(id=category_id)
            category_name = category.name
            
            # Vérifier s'il y a des sites dans cette catégorie
            if category.sites.exists():
                return JsonResponse({
                    'success': False, 
                    'error': f'Impossible de supprimer la catégorie "{category_name}" car elle contient des sites.'
                })
            
            category.delete()
            return JsonResponse({'success': True, 'message': f'Catégorie "{category_name}" supprimée avec succès.'})
        except TouristSiteCategory.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Catégorie non trouvée.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'})


@login_required
@user_passes_test(is_super_admin)
def super_admin_site_create(request):
    """Créer un nouveau site touristique"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            category_id = request.POST.get('category')
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            is_active = request.POST.get('is_active') == 'on'
            
            if not all([name, description, latitude, longitude]):
                return JsonResponse({'success': False, 'error': 'Tous les champs obligatoires doivent être remplis.'})
            
            # Créer le site
            site_data = {
                'name': name,
                'description': description,
                'latitude': latitude,
                'longitude': longitude,
                'is_active': is_active
            }
            
            if category_id:
                try:
                    category = TouristSiteCategory.objects.get(id=category_id)
                    site_data['category'] = category
                except TouristSiteCategory.DoesNotExist:
                    pass
            
            site = TouristSite.objects.create(**site_data)

            return JsonResponse({
                'success': True, 
                'message': f'Site "{name}" créé avec succès.',
                'site_id': site.id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'})


@login_required
@user_passes_test(is_super_admin)
def super_admin_site_edit(request, site_id):
    """Édition d'un site touristique (AJAX POST)"""
    if request.method == 'POST':
        try:
            site = TouristSite.objects.get(id=site_id)
            site.name = request.POST.get('name')
            site.description = request.POST.get('description')
            category_id = request.POST.get('category')
            site.category = TouristSiteCategory.objects.get(id=category_id) if category_id else None
            site.latitude = request.POST.get('latitude')
            site.longitude = request.POST.get('longitude')
            site.is_active = request.POST.get('is_active') == 'on'
            site.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'})


@login_required
@user_passes_test(is_super_admin)
def super_admin_category_detail_api(request, category_id):
    """API JSON pour le détail d'une catégorie (modale édition)"""
    try:
        category = TouristSiteCategory.objects.get(id=category_id)
        data = {
            'id': category.id,
            'name': category.name,
            'description': category.description,
        }
        return JsonResponse({'success': True, 'category': data})
    except TouristSiteCategory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Catégorie non trouvée.'})


@login_required
@user_passes_test(is_super_admin)
def super_admin_category_edit(request, category_id):
    """Édition d'une catégorie (AJAX POST)"""
    if request.method == 'POST':
        try:
            category = TouristSiteCategory.objects.get(id=category_id)
            category.name = request.POST.get('name')
            category.description = request.POST.get('description')
            category.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'})


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Rayon de la Terre en mètres
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c


@login_required
@user_passes_test(is_super_admin)
def super_admin_zones_dangereuses_create(request):
    """Créer une nouvelle zone dangereuse (AJAX POST)"""
    if request.method == 'POST':
        nom_zone = request.POST.get('nom_zone')
        site = request.POST.get('site')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        print(f"[DEBUG] nom_zone: {nom_zone}, site: {site}, latitude: {latitude}, longitude: {longitude}")
        print(f"[DEBUG] site.id: {site if site else None}")
        from apps.tourist_sites.models import ZoneDangereuse
        # Vérification doublon géographique (moins de 100m)
        doublon = False
        if latitude and longitude:
            for zone in ZoneDangereuse.objects.all():
                if zone.latitude and zone.longitude:
                    if haversine(latitude, longitude, zone.latitude, zone.longitude) < 100:
                        doublon = True
                        break
        if doublon:
            return JsonResponse({'success': False, 'error': 'Attention ! Une zone similaire existe déjà à proximité.'})
        # (On peut garder la vérification par nom+site si besoin, mais la vérification géographique est prioritaire)
        zone = ZoneDangereuse(nom_zone=nom_zone, latitude=latitude, longitude=longitude, guide_rapporteur=request.user)
        try:
            zone.save()
            print("Zone créée avec ID:", zone.id_zonedangereuse)
        except Exception as e:
            print("Erreur lors du save:", e)
            return JsonResponse({'success': False, 'error': f'Erreur lors du save: {e}'})
        return JsonResponse({'success': True, 'message': f'Zone dangereuse "{zone.nom_zone}" créée avec succès.'})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'})


@login_required
@user_passes_test(is_super_admin)
def super_admin_zones_dangereuses_list(request):
    """Liste complète des zones dangereuses pour le super admin"""
    zones = ZoneDangereuse.objects.all().select_related('site', 'guide_rapporteur').order_by('-date_signalement')
    
    # Filtres
    statut = request.GET.get('statut')
    type_danger = request.GET.get('type_danger')
    search = request.GET.get('search')
    
    if statut:
        zones = zones.filter(statut=statut)
    
    if type_danger:
        zones = zones.filter(type_danger=type_danger)
    
    if search:
        zones = zones.filter(
            Q(nom_zone__icontains=search) | 
            Q(description_danger__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(zones, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques pour les filtres
    stats = {
        'total': ZoneDangereuse.objects.count(),
        'signalees': ZoneDangereuse.objects.filter(statut=ZoneDangereuse.Statut.SIGNALEE).count(),
        'verifiees': ZoneDangereuse.objects.filter(statut=ZoneDangereuse.Statut.VERIFIEE).count(),
        'resolues': ZoneDangereuse.objects.filter(statut=ZoneDangereuse.Statut.RESOLUE).count(),
        'rejetees': ZoneDangereuse.objects.filter(statut=ZoneDangereuse.Statut.REJETEE).count(),
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'selected_statut': statut,
        'selected_type_danger': type_danger,
        'search': search,
        'statut_choices': ZoneDangereuse.Statut.choices,
        'type_danger_choices': ZoneDangereuse._meta.get_field('type_danger').choices,
    }
    return render(request, 'tourist_sites/admin/super_admin_zones_list.html', context)


# --- VUES POUR LES ZONES DANGEREUSES ---

@login_required
@user_passes_test(is_super_admin)
def zone_dangereuse_detail(request, zone_id):
    """Vue de détail d'une zone dangereuse"""
    try:
        zone = ZoneDangereuse.objects.get(id_zonedangereuse=zone_id)
        return render(request, 'tourist_sites/admin/zone_dangereuse_detail.html', {
            'zone': zone
        })
    except ZoneDangereuse.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Zone dangereuse non trouvée.'})


@login_required
@user_passes_test(is_super_admin)
def zone_dangereuse_edit(request, zone_id):
    """Vue d'édition d'une zone dangereuse"""
    try:
        zone = ZoneDangereuse.objects.get(id_zonedangereuse=zone_id)
        return render(request, 'tourist_sites/admin/zone_dangereuse_edit.html', {
            'zone': zone,
        })
    except ZoneDangereuse.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Zone dangereuse non trouvée.'})


@login_required
@user_passes_test(is_super_admin)
def zone_dangereuse_delete(request, zone_id):
    """Supprimer une zone dangereuse"""
    if request.method == 'POST':
        try:
            zone = ZoneDangereuse.objects.get(id_zonedangereuse=zone_id)
            zone.delete()
            return JsonResponse({'success': True, 'message': 'Zone dangereuse supprimée avec succès.'})
        except ZoneDangereuse.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Zone dangereuse non trouvée.'})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'})


@login_required
@user_passes_test(is_super_admin)
def zone_dangereuse_validate(request, zone_id):
    """Valider une zone dangereuse (changer statut en VÉRIFIÉE)"""
    if request.method == 'POST':
        try:
            zone = ZoneDangereuse.objects.get(id_zonedangereuse=zone_id)
            zone.statut = 'VERIFIEE'
            zone.save()
            return JsonResponse({'success': True, 'message': 'Zone dangereuse validée avec succès.'})
        except ZoneDangereuse.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Zone dangereuse non trouvée.'})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'})


@login_required
@user_passes_test(is_super_admin)
def zone_dangereuse_resolve(request, zone_id):
    """Marquer une zone dangereuse comme résolue"""
    if request.method == 'POST':
        try:
            zone = ZoneDangereuse.objects.get(id_zonedangereuse=zone_id)
            zone.statut = 'RESOLUE'
            zone.save()
            return JsonResponse({'success': True, 'message': 'Zone dangereuse marquée comme résolue.'})
        except ZoneDangereuse.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Zone dangereuse non trouvée.'})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'})


@login_required
@user_passes_test(is_super_admin)
def zone_dangereuse_detail_api(request, zone_id):
    """API pour récupérer les détails d'une zone dangereuse"""
    try:
        zone = ZoneDangereuse.objects.get(id_zonedangereuse=zone_id)
        return JsonResponse({
            'success': True,
            'zone': {
                'id': zone.id_zonedangereuse,
                'nom_zone': zone.nom_zone,
                'type_danger': zone.type_danger,
                'description_danger': zone.description_danger,
                'latitude': float(zone.latitude) if zone.latitude else None,
                'longitude': float(zone.longitude) if zone.longitude else None,
                'site_id': zone.site.id if zone.site else None,
                'statut': zone.statut,
                'date_signalement': zone.date_signalement.isoformat(),
            }
        })
    except ZoneDangereuse.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Zone dangereuse non trouvée.'})


@login_required
def zone_dangereuse_detail_vote(request, zone_id):
    zone = get_object_or_404(ZoneDangereuse, id_zonedangereuse=zone_id)
    user = request.user
    user_vote = None
    if request.method == 'POST':
        vote_type = request.POST.get('vote')
        if vote_type in ['like', 'dislike']:
            # Vérifie si l'utilisateur a déjà voté
            user_vote = ZoneDangereuseVote.objects.filter(zone=zone, utilisateur=user).first()
            if not user_vote:
                ZoneDangereuseVote.objects.create(
                    zone=zone,
                    utilisateur=user,
                    is_like=(vote_type == 'like')
                )
                messages.success(request, "Merci pour votre vote !")
                return redirect('zone_dangereuse_detail_vote', zone_id=zone.id_zonedangereuse)
            else:
                messages.warning(request, "Vous avez déjà voté pour cette zone.")
    # Récupère les votes
    likes = zone.get_likes_count()
    dislikes = zone.get_dislikes_count()
    user_vote = ZoneDangereuseVote.objects.filter(zone=zone, utilisateur=user).first()
    context = {
        'zone': zone,
        'likes': likes,
        'dislikes': dislikes,
        'user_vote': user_vote,
    }
    return render(request, 'tourist_sites/zone_dangereuse_detail_vote.html', context) 


@login_required
@require_POST
def vote_zone_dangereuse(request, zone_id):
    print(f'[DEBUG] Vote zone dangereuse - Zone ID: {zone_id}, User: {request.user}')
    user = request.user
    try:
        zone = ZoneDangereuse.objects.get(id_zonedangereuse=zone_id)
        print(f'[DEBUG] Zone trouvée: {zone.nom_zone}')
    except ZoneDangereuse.DoesNotExist:
        print(f'[DEBUG] Zone non trouvée pour ID: {zone_id}')
        return JsonResponse({'success': False, 'error': 'Zone dangereuse non trouvée.'}, status=404)
    
    try:
        import json
        data = json.loads(request.body)
        vote_type = data.get('vote')
        print(f'[DEBUG] Vote type reçu: {vote_type}')
        
        if vote_type not in ['like', 'dislike']:
            print(f'[DEBUG] Type de vote invalide: {vote_type}')
            return JsonResponse({'success': False, 'error': 'Type de vote invalide.'}, status=400)
        
        is_like = (vote_type == 'like')
        print(f'[DEBUG] is_like: {is_like}')
        
        try:
            # Essayer de créer ou mettre à jour le vote
            vote, created = ZoneDangereuseVote.objects.get_or_create(
                zone=zone, 
                utilisateur=user,
                defaults={'is_like': is_like}
            )
            
            if created:
                print(f'[DEBUG] Nouveau vote créé')
            else:
                # L'utilisateur a déjà voté, vérifier s'il change son vote
                if vote.is_like == is_like:
                    print(f'[DEBUG] Utilisateur a déjà voté de cette façon')
                    return JsonResponse({'success': False, 'error': 'Vous avez déjà voté de cette façon pour cette zone.'}, status=400)
                else:
                    # Changer le vote
                    print(f'[DEBUG] Changement de vote de {vote.is_like} vers {is_like}')
                    vote.is_like = is_like
                    vote.save()
            
            # Vérifier le seuil de validation
            zone.check_validation(seuil=3)
            
            likes = zone.get_likes_count()
            dislikes = zone.get_dislikes_count()
            print(f'[DEBUG] Résultat - Likes: {likes}, Dislikes: {dislikes}')
            
            return JsonResponse({
                'success': True,
                'likes': likes,
                'dislikes': dislikes,
                'message': 'Vote enregistré.'
            })
            
        except Exception as vote_error:
            print(f'[DEBUG] Erreur lors de la création/mise à jour du vote: {str(vote_error)}')
            return JsonResponse({'success': False, 'error': f'Erreur lors du vote: {str(vote_error)}'}, status=500)
            
    except Exception as e:
        print(f'[DEBUG] Erreur lors du vote: {str(e)}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def signaler_zone_dangereuse(request):
    user = request.user
    nom_zone = request.POST.get('nom_zone')
    type_danger = request.POST.get('type_danger')
    description_danger = request.POST.get('description_danger')
    latitude = request.POST.get('latitude')
    longitude = request.POST.get('longitude')
    site_id = request.POST.get('site_id')
    image = request.FILES.get('image')

    if not (nom_zone and type_danger and description_danger and latitude and longitude):
        print('[DEBUG] Signalement zone échoué : champs manquants')
        return JsonResponse({'success': False, 'error': "Champs obligatoires manquants."}, status=400)

    try:
        site = TouristSite.objects.get(id=site_id) if site_id else None
        zone = ZoneDangereuse.objects.create(
            nom_zone=nom_zone,
            type_danger=type_danger,
            description_danger=description_danger,
            latitude=latitude,
            longitude=longitude,
            guide_rapporteur=user,
            image=image,
            site=site
        )
        print(f'[DEBUG] Nouvelle zone dangereuse ajoutée : {zone.nom_zone} ({zone.latitude}, {zone.longitude}) par {user}')
        # Notification utilisateur
        Notification.objects.create(
            destinataire=user,
            message="Votre signalement de zone dangereuse a bien été pris en compte.",
            url=reverse('tourist_sites:sites_list') + f"?zone_id={zone.id_zonedangereuse}",
        )
        return JsonResponse({
            'success': True,
            'zone': {
                'id': zone.id_zonedangereuse,
                'nom_zone': zone.nom_zone,
                'type_danger': zone.type_danger,
                'description_danger': zone.description_danger,
                'latitude': float(zone.latitude),
                'longitude': float(zone.longitude),
                'image_url': zone.image.url if zone.image else None,
                'statut': zone.statut,
                'site_id': site.id if site else None,
                'site_name': site.name if site else None,
            }
        })
    except Exception as e:
        print(f'[DEBUG] Erreur lors du signalement de zone : {e}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500) 