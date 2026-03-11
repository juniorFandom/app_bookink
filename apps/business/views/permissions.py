from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from ..models import BusinessLocation, BusinessPermission, PermissionRequest, Business, UserActionLog
from ..forms import BusinessPermissionForm, UserSearchForm, PermissionReviewForm, PermissionRequestForm

User = get_user_model()


@login_required
def permission_list(request, location_pk):
    """
    List all permissions for a business location
    """
    location = get_object_or_404(BusinessLocation, pk=location_pk)
    
    # Check if user is the owner
    if location.business.owner != request.user:
        messages.error(request, _('You do not have permission to view permissions for this location.'))
        return redirect('business:location_detail', pk=location.pk)
    
    permissions = BusinessPermission.objects.filter(
        business_location=location
    ).select_related('user', 'granted_by').order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status', '')
    if status == 'active':
        permissions = permissions.filter(is_active=True)
    elif status == 'expired':
        permissions = permissions.filter(is_active=False)
    
    # Filter by permission type
    permission_type = request.GET.get('permission_type', '')
    if permission_type:
        permissions = permissions.filter(permission_type=permission_type)
    
    paginator = Paginator(permissions, 20)
    page = request.GET.get('page')
    permissions = paginator.get_page(page)
    
    context = {
        'location': location,
        'permissions': permissions,
        'permission_types': BusinessPermission.PERMISSION_TYPES,
        'status_filter': status,
        'permission_type_filter': permission_type,
    }
    return render(request, 'business/permissions/permission_list.html', context)


@login_required
def permission_create(request, location_pk):
    """
    Create a new permission for a business location
    """
    location = get_object_or_404(BusinessLocation, pk=location_pk)
    
    # Check if user is the owner
    if location.business.owner != request.user:
        messages.error(request, _('You do not have permission to create permissions for this location.'))
        return redirect('business:location_detail', pk=location.pk)
    
    if request.method == 'POST':
        form = BusinessPermissionForm(request.POST, business_location=location)
        if form.is_valid():
            permission = form.save(commit=False)
            permission.business_location = location
            permission.granted_by = request.user
            permission.save()
            
            messages.success(request, _('Permission granted successfully.'))
            return redirect('business:permission_list', location_pk=location.pk)
    else:
        form = BusinessPermissionForm(business_location=location)
    
    context = {
        'form': form,
        'location': location,
        'title': _('Grant Permission'),
    }
    return render(request, 'business/permissions/permission_form.html', context)


@login_required
def permission_edit(request, permission_pk):
    """
    Edit an existing permission
    """
    permission = get_object_or_404(BusinessPermission, pk=permission_pk)
    location = permission.business_location
    
    # Check if user is the owner
    if location.business.owner != request.user:
        messages.error(request, _('You do not have permission to edit this permission.'))
        return redirect('business:location_detail', pk=location.pk)
    
    if request.method == 'POST':
        form = BusinessPermissionForm(request.POST, instance=permission, business_location=location)
        if form.is_valid():
            form.save()
            messages.success(request, _('Permission updated successfully.'))
            return redirect('business:permission_list', location_pk=location.pk)
    else:
        form = BusinessPermissionForm(instance=permission, business_location=location)
    
    context = {
        'form': form,
        'permission': permission,
        'location': location,
        'title': _('Edit Permission'),
    }
    return render(request, 'business/permissions/permission_form.html', context)


@login_required
@require_POST
def permission_delete(request, permission_pk):
    """
    Delete a permission
    """
    permission = get_object_or_404(BusinessPermission, pk=permission_pk)
    location = permission.business_location
    
    # Check if user is the owner
    if location.business.owner != request.user:
        messages.error(request, _('You do not have permission to delete this permission.'))
        return redirect('business:location_detail', pk=location.pk)
    
    permission.delete()
    messages.success(request, _('Permission revoked successfully.'))
    return redirect('business:permission_list', location_pk=location.pk)


@login_required
def user_search(request, location_pk):
    """
    Search for users to assign permissions
    """
    location = get_object_or_404(BusinessLocation, pk=location_pk)
    
    # Check if user is the owner
    if location.business.owner != request.user:
        messages.error(request, _('You do not have permission to search users for this location.'))
        return redirect('business:location_detail', pk=location.pk)
    
    users = []
    search_query = ''
    
    if request.method == 'POST':
        form = UserSearchForm(request.POST)
        if form.is_valid():
            search_query = form.cleaned_data['search']
            if search_query:
                users = User.objects.filter(
                    Q(username__icontains=search_query) |
                    Q(email__icontains=search_query) |
                    Q(first_name__icontains=search_query) |
                    Q(last_name__icontains=search_query)
                ).exclude(
                    id=request.user.id  # Exclude current user
                ).exclude(
                    business_permissions__business_location=location  # Exclude users who already have permissions
                )[:10]
    else:
        form = UserSearchForm()
    
    context = {
        'form': form,
        'users': users,
        'location': location,
        'search_query': search_query,
    }
    return render(request, 'business/permissions/user_search.html', context)


@login_required
def permission_request_list(request):
    """
    List permission requests for business locations owned by the user
    """
    # Get business locations owned by the user
    owned_locations = BusinessLocation.objects.filter(business__owner=request.user)
    
    # Get pending requests for these locations
    requests = PermissionRequest.objects.filter(
        business_location__in=owned_locations,
        status='pending'
    ).select_related('business_location', 'requester').order_by('-created_at')
    
    # Get all requests (pending, approved, rejected)
    all_requests = PermissionRequest.objects.filter(
        business_location__in=owned_locations
    ).select_related('business_location', 'requester', 'reviewed_by').order_by('-created_at')
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        all_requests = all_requests.filter(status=status_filter)
    
    paginator = Paginator(all_requests, 20)
    page = request.GET.get('page')
    all_requests = paginator.get_page(page)
    
    context = {
        'requests': requests,
        'all_requests': all_requests,
        'status_filter': status_filter,
    }
    return render(request, 'business/permissions/request_list.html', context)


@login_required
def permission_request_detail(request, request_pk):
    """
    View and review a permission request
    """
    permission_request = get_object_or_404(PermissionRequest, pk=request_pk)
    location = permission_request.business_location
    
    # Check if user is the owner
    if location.business.owner != request.user:
        messages.error(request, _('You do not have permission to view this request.'))
        return redirect('business:permission_request_list')
    
    if request.method == 'POST':
        form = PermissionReviewForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            notes = form.cleaned_data['notes']
            
            if action == 'approve':
                permission_request.approve(request.user, notes)
                messages.success(request, _('Permission request approved.'))
            else:
                permission_request.reject(request.user, notes)
                messages.success(request, _('Permission request rejected.'))
            
            return redirect('business:permission_request_list')
    else:
        form = PermissionReviewForm()
    
    context = {
        'permission_request': permission_request,
        'form': form,
        'location': location,
    }
    return render(request, 'business/permissions/request_detail.html', context)


@login_required
def my_permissions(request):
    """
    List permissions granted to the current user
    """
    permissions = BusinessPermission.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('business_location', 'business_location__business', 'granted_by').order_by('-created_at')
    
    # Filter by business location
    location_filter = request.GET.get('location', '')
    if location_filter:
        permissions = permissions.filter(business_location_id=location_filter)
    
    # Filter by permission type
    permission_type_filter = request.GET.get('permission_type', '')
    if permission_type_filter:
        permissions = permissions.filter(permission_type=permission_type_filter)
    
    paginator = Paginator(permissions, 20)
    page = request.GET.get('page')
    permissions = paginator.get_page(page)
    
    # Get user's business locations for filter
    user_locations = BusinessLocation.objects.filter(
        permissions__user=request.user,
        permissions__is_active=True
    ).distinct()
    
    context = {
        'permissions': permissions,
        'user_locations': user_locations,
        'permission_types': BusinessPermission.PERMISSION_TYPES,
        'location_filter': location_filter,
        'permission_type_filter': permission_type_filter,
    }
    return render(request, 'business/permissions/my_permissions.html', context)


@login_required
def request_permission(request):
    """
    Request permission for a business location
    """
    if request.method == 'POST':
        form = PermissionRequestForm(request.POST, user=request.user)
        if form.is_valid():
            permission_request = form.save(commit=False)
            permission_request.requester = request.user
            permission_request.save()
            
            messages.success(request, _('Permission request submitted successfully.'))
            return redirect('business:my_permissions')
    else:
        form = PermissionRequestForm(user=request.user)
    
    context = {
        'form': form,
        'title': _('Request Permission'),
    }
    return render(request, 'business/permissions/request_permission.html', context)


def check_permission(user, location, permission_type):
    """
    Vérifie si un utilisateur a une permission spécifique pour un établissement
    """
    if not user.is_authenticated:
        return False
    
    # Le propriétaire a toujours tous les droits
    if location.business.owner == user:
        return True
    
    # Vérifier les permissions accordées
    permission = BusinessPermission.objects.filter(
        business_location=location,
        user=user,
        permission_type=permission_type,
        is_active=True
    ).first()
    
    if not permission:
        return False
    
    # Vérifier si la permission n'est pas expirée
    if permission.expires_at and permission.expires_at < timezone.now():
        return False
    
    return True


def has_any_permission(user, location):
    """
    Vérifie si un utilisateur a au moins une permission pour un établissement
    """
    if not user.is_authenticated:
        return False
    
    # Le propriétaire a toujours tous les droits
    if location.business.owner == user:
        return True
    
    # Vérifier s'il a au moins une permission active
    return BusinessPermission.objects.filter(
        business_location=location,
        user=user,
        is_active=True
    ).exists()


def require_permission(permission_type):
    """
    Décorateur pour protéger les vues avec une vérification de permission
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Récupérer l'ID de l'établissement depuis les paramètres
            location_pk = kwargs.get('location_pk') or kwargs.get('pk')
            
            if not location_pk:
                messages.error(request, _('Paramètre d\'établissement manquant.'))
                return redirect('business:my_businesses')
            
            try:
                location = BusinessLocation.objects.get(pk=location_pk)
            except BusinessLocation.DoesNotExist:
                messages.error(request, _('Établissement non trouvé.'))
                return redirect('business:my_businesses')
            
            # Vérifier la permission
            if not check_permission(request.user, location, permission_type):
                messages.error(request, _('Vous n\'avez pas la permission d\'accéder à cette fonctionnalité.'))
                return redirect('business:my_permissions')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_user_permissions(user):
    """
    Récupère toutes les permissions actives d'un utilisateur
    """
    if not user.is_authenticated:
        return BusinessPermission.objects.none()
    
    return BusinessPermission.objects.filter(
        user=user,
        is_active=True
    ).select_related('business_location', 'business_location__business')


def get_accessible_locations(user):
    """
    Récupère tous les établissements auxquels un utilisateur a accès
    """
    if not user.is_authenticated:
        return BusinessLocation.objects.none()
    
    # Établissements dont l'utilisateur est propriétaire
    owned_locations = BusinessLocation.objects.filter(business__owner=user)
    
    # Établissements pour lesquels l'utilisateur a des permissions
    permission_locations = BusinessLocation.objects.filter(
        permissions__user=user,
        permissions__is_active=True
    )
    
    # Combiner et dédupliquer
    return (owned_locations | permission_locations).distinct()


@login_required
def access_management(request):
    """
    Interface d'administration des accès pour les propriétaires
    """
    # Vérifier si l'utilisateur est propriétaire d'au moins une business
    owned_businesses = Business.objects.filter(owner=request.user)
    
    if not owned_businesses.exists():
        messages.error(request, _('Vous devez être propriétaire d\'au moins une entreprise pour accéder à cette fonctionnalité.'))
        return redirect('business:my_permissions')
    
    # Récupérer toutes les business locations du propriétaire
    business_locations = BusinessLocation.objects.filter(
        business__owner=request.user
    ).select_related('business').prefetch_related('permissions__user').order_by('business__name', 'name')
    
    # Statistiques
    total_locations = business_locations.count()
    total_permissions = BusinessPermission.objects.filter(
        business_location__business__owner=request.user
    ).count()
    active_permissions = BusinessPermission.objects.filter(
        business_location__business__owner=request.user,
        is_active=True
    ).count()
    
    context = {
        'business_locations': business_locations,
        'total_locations': total_locations,
        'total_permissions': total_permissions,
        'active_permissions': active_permissions,
        'owned_businesses': owned_businesses,
    }
    return render(request, 'business/permissions/access_management.html', context)


@login_required
def manage_location_access(request, location_pk):
    """
    Gérer les accès pour une business location spécifique
    """
    location = get_object_or_404(BusinessLocation, pk=location_pk)
    
    # Vérifier si l'utilisateur est le propriétaire
    if location.business.owner != request.user:
        messages.error(request, _('Vous n\'avez pas la permission de gérer les accès pour cette établissement.'))
        return redirect('business:access_management')
    
    # Récupérer les permissions existantes
    permissions = BusinessPermission.objects.filter(
        business_location=location
    ).select_related('user', 'granted_by').order_by('-created_at')
    
    # Recherche d'utilisateurs
    users = []
    search_query = ''
    
    if request.method == 'POST':
        search_query = request.POST.get('search', '').strip()
        if search_query:
            users = User.objects.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            ).exclude(
                id=request.user.id  # Exclure le propriétaire
            ).exclude(
                business_permissions__business_location=location  # Exclure ceux qui ont déjà des permissions
            )[:10]
    
    # Filtrer les permissions selon le type d'établissement
    location_type = location.business_location_type
    if location_type == 'hotel':
        available_permissions = BusinessPermission.GENERAL_PERMISSIONS + BusinessPermission.HOTEL_PERMISSIONS
    elif location_type == 'restaurant':
        available_permissions = BusinessPermission.GENERAL_PERMISSIONS + BusinessPermission.RESTAURANT_PERMISSIONS
    elif location_type == 'vehicle_rental':
        available_permissions = BusinessPermission.GENERAL_PERMISSIONS + BusinessPermission.VEHICLE_PERMISSIONS
    elif location_type == 'tour':
        available_permissions = BusinessPermission.GENERAL_PERMISSIONS + BusinessPermission.TOUR_PERMISSIONS
    else:
        available_permissions = BusinessPermission.GENERAL_PERMISSIONS
    
    context = {
        'location': location,
        'permissions': permissions,
        'users': users,
        'search_query': search_query,
        'permission_types': available_permissions,
    }
    return render(request, 'business/permissions/manage_location_access.html', context)


@login_required
@require_POST
def quick_grant_permission(request, location_pk):
    """
    Accorder rapidement une permission
    """
    location = get_object_or_404(BusinessLocation, pk=location_pk)
    
    # Vérifier si l'utilisateur est le propriétaire
    if location.business.owner != request.user:
        return JsonResponse({'error': _('Permission refusée')}, status=403)
    
    user_id = request.POST.get('user_id')
    permission_type = request.POST.get('permission_type')
    duration = request.POST.get('duration', 'custom')
    custom_date = request.POST.get('custom_date', '')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': _('Utilisateur non trouvé')}, status=404)
    
    # Calculer la date d'expiration
    expires_at = None
    if duration != 'permanent':
        if duration == 'custom' and custom_date:
            try:
                expires_at = timezone.datetime.fromisoformat(custom_date.replace('Z', '+00:00'))
            except ValueError:
                return JsonResponse({'error': _('Date invalide')}, status=400)
        else:
            # Durées prédéfinies
            duration_map = {
                '1_month': 30,
                '3_months': 90,
                '6_months': 180,
                '1_year': 365,
            }
            if duration in duration_map:
                expires_at = timezone.now() + timezone.timedelta(days=duration_map[duration])
    
    # Créer la permission
    try:
        permission = BusinessPermission.objects.create(
            business_location=location,
            user=user,
            permission_type=permission_type,
            granted_by=request.user,
            expires_at=expires_at,
            notes=f"Permission accordée rapidement par {request.user.get_full_name() or request.user.username}"
        )
        
        return JsonResponse({
            'success': True,
            'message': _('Permission accordée avec succès'),
            'permission_id': permission.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def quick_revoke_permission(request, permission_pk):
    """
    Révoquer rapidement une permission
    """
    permission = get_object_or_404(BusinessPermission, pk=permission_pk)
    
    # Vérifier si l'utilisateur est le propriétaire
    if permission.business_location.business.owner != request.user:
        return JsonResponse({'error': _('Permission refusée')}, status=403)
    
    try:
        permission.delete()
        return JsonResponse({
            'success': True,
            'message': _('Permission révoquée avec succès')
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def log_user_action(user, location, action_type, description, request=None):
    """
    Trace une action utilisateur dans le journal
    """
    ip_address = None
    user_agent = ''
    
    if request:
        ip_address = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    UserActionLog.objects.create(
        user=user,
        business_location=location,
        action_type=action_type,
        action_description=description,
        ip_address=ip_address,
        user_agent=user_agent
    )


def get_user_action_logs(user, location=None, action_type=None, limit=50):
    """
    Récupère les logs d'actions d'un utilisateur
    """
    queryset = UserActionLog.objects.filter(user=user)
    
    if location:
        queryset = queryset.filter(business_location=location)
    
    if action_type:
        queryset = queryset.filter(action_type=action_type)
    
    return queryset.order_by('-created_at')[:limit]


@login_required
def action_logs(request, location_pk=None):
    """
    Affiche les logs d'actions des utilisateurs
    """
    from ..models import UserActionLog
    
    # Si location_pk est fourni, vérifier les permissions
    if location_pk:
        location = get_object_or_404(BusinessLocation, pk=location_pk)
        if not (location.business.owner == request.user or has_any_permission(request.user, location)):
            messages.error(request, _('Vous n\'avez pas la permission de voir les logs de cet établissement.'))
            return redirect('business:my_permissions')
        
        logs_qs = UserActionLog.objects.filter(business_location=location)
    else:
        # Afficher tous les logs des établissements accessibles
        accessible_locations = get_accessible_locations(request.user)
        logs_qs = UserActionLog.objects.filter(business_location__in=accessible_locations)
    
    # Filtres
    action_type = request.GET.get('action_type', '')
    user_id = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if action_type:
        logs_qs = logs_qs.filter(action_type=action_type)
    
    if user_id:
        logs_qs = logs_qs.filter(user_id=user_id)
    
    if date_from:
        logs_qs = logs_qs.filter(created_at__gte=date_from)
    
    if date_to:
        logs_qs = logs_qs.filter(created_at__lte=date_to)
    
    # Statistiques (calculées sur la queryset complète, avant pagination)
    total_actions = logs_qs.count()
    unique_users = logs_qs.values('user').distinct().count()
    
    # Pagination
    paginator = Paginator(logs_qs.select_related('user', 'business_location', 'business_location__business'), 50)
    page = request.GET.get('page')
    logs = paginator.get_page(page)
    
    context = {
        'logs': logs,
        'total_actions': total_actions,
        'unique_users': unique_users,
        'action_types': UserActionLog.ACTION_TYPES,
        'location': location if location_pk else None,
        'filters': {
            'action_type': action_type,
            'user_id': user_id,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    return render(request, 'business/permissions/action_logs.html', context) 