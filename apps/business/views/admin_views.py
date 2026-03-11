from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal
import json

from apps.business.models import BusinessLocation, BusinessPermission
from apps.wallets.models import UserTransaction
from apps.wallets.models.wallet import BusinessLocationWallet

from apps.users.models import User
from apps.rooms.models import RoomBooking
from apps.orders.models import RestaurantOrder
from apps.tours.models import TourBooking
from apps.vehicles.models import VehicleBooking
from apps.tourist_sites.models import TouristSite, TouristSiteCategory, ZoneDangereuse

def is_superuser(user):
    """Vérifie si l'utilisateur est super utilisateur"""
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def super_admin_dashboard(request):
    """Dashboard principal pour le super administrateur"""
    
    # Statistiques globales
    total_businesses = BusinessLocation.objects.count()
    total_users = User.objects.count()
    pending_approvals = BusinessLocation.objects.filter(is_verified=False).count()
    active_businesses = BusinessLocation.objects.filter(is_active=True).count()
    
    # Statistiques des transactions
    today = timezone.now().date()
    this_month = timezone.now().replace(day=1)
    
    # Transactions du mois
    monthly_transactions = UserTransaction.objects.filter(
        created_at__gte=this_month,
        status='COMPLETED'
    )
    
    total_monthly_amount = monthly_transactions.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Utiliser le service de commission pour les statistiques
    from apps.wallets.services.commission_service import CommissionService
    commission_stats = CommissionService.get_commission_statistics()
    monthly_commission = commission_stats['monthly_commission']
    
    # Ajout du total des wallets et de la commission 5%
    total_wallets_balance = BusinessLocationWallet.objects.aggregate(total=Sum('balance'))['total'] or 0
    commission_wallets = total_wallets_balance * Decimal('0.05')
    
    # Business locations en attente d'approbation
    pending_businesses = BusinessLocation.objects.filter(
        is_verified=False
    ).select_related('business', 'owner').order_by('-created_at')[:10]
    
    # Dernières transactions
    recent_transactions = UserTransaction.objects.filter(
        status='COMPLETED'
    ).order_by('-created_at')[:10]
    
    # Statistiques par type de business
    business_types_stats = BusinessLocation.objects.values('business_location_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Données pour les graphiques
    chart_data = get_chart_data()
    
    # Données des sites touristiques
    tourist_sites = TouristSite.objects.all().select_related('category').order_by('-created_at')
    categories = TouristSiteCategory.objects.all().order_by('name')
    categories_json = list(categories.values('id', 'name'))
    
    # Données des zones dangereuses
    total_zones = ZoneDangereuse.objects.count()
    zones_signalees = ZoneDangereuse.objects.filter(statut=ZoneDangereuse.Statut.SIGNALEE).count()
    zones_verifiees = ZoneDangereuse.objects.filter(statut=ZoneDangereuse.Statut.VERIFIEE).count()
    zones_resolues = ZoneDangereuse.objects.filter(statut=ZoneDangereuse.Statut.RESOLUE).count()
    recent_zones = ZoneDangereuse.objects.all().select_related('site', 'guide_rapporteur').order_by('-date_signalement')[:5]
    
    context = {
        'total_businesses': total_businesses,
        'total_users': total_users,
        'pending_approvals': pending_approvals,
        'active_businesses': active_businesses,
        'total_monthly_amount': total_monthly_amount,
        'monthly_commission': monthly_commission,
        'pending_businesses': pending_businesses,
        'recent_transactions': recent_transactions,
        'business_types_stats': business_types_stats,
        'chart_data': chart_data,
        'tourist_sites': tourist_sites,
        'categories': categories,
        'categories_json': categories_json,
        'total_zones': total_zones,
        'zones_signalees': zones_signalees,
        'zones_verifiees': zones_verifiees,
        'zones_resolues': zones_resolues,
        'recent_zones': recent_zones,
        'total_wallets_balance': total_wallets_balance,
        'commission_wallets': commission_wallets,
    }
    
    return render(request, 'business/admin/super_admin_dashboard.html', context)

@login_required
@user_passes_test(is_superuser)
def super_admin_wallet(request):
    """Gestion du wallet du super administrateur"""
    
    # Transactions de commission
    commission_transactions = UserTransaction.objects.filter(
        transaction_type='COMMISSION',
        status='COMPLETED'
    ).order_by('-created_at')
    
    # Statistiques des commissions
    total_commission = commission_transactions.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    monthly_commission = commission_transactions.filter(
        created_at__gte=timezone.now().replace(day=1)
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Créer un objet wallet virtuel pour le super admin
    super_admin_wallet = {
        'balance': total_commission,
        'id': 'super_admin',
        'name': 'Super Admin Wallet'
    }
    
    context = {
        'wallet': super_admin_wallet,
        'commission_transactions': commission_transactions,
        'total_commission': total_commission,
        'monthly_commission': monthly_commission,
    }
    
    return render(request, 'business/admin/super_admin_wallet.html', context)

@login_required
@user_passes_test(is_superuser)
def approve_business_location(request, pk):
    """Approuver un business location"""
    if request.method == 'POST':
        business_location = get_object_or_404(BusinessLocation, pk=pk)
        business_location.is_verified = True
        business_location.save()
        
        messages.success(request, f'Business location "{business_location.name}" approuvé avec succès!')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False}, status=400)

@login_required
@user_passes_test(is_superuser)
def reject_business_location(request, pk):
    """Rejeter un business location"""
    if request.method == 'POST':
        business_location = get_object_or_404(BusinessLocation, pk=pk)
        reason = request.POST.get('reason', '')
        
        # Marquer comme rejeté (vous pouvez ajouter un champ is_rejected si nécessaire)
        business_location.is_active = False
        business_location.save()
        
        messages.warning(request, f'Business location "{business_location.name}" rejeté. Raison: {reason}')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False}, status=400)

@login_required
@user_passes_test(is_superuser)
def business_approval_list(request):
    """Liste des business locations en attente d'approbation"""
    
    pending_businesses = BusinessLocation.objects.filter(
        is_verified=False
    ).select_related('business', 'owner').order_by('-created_at')
    
    context = {
        'pending_businesses': pending_businesses,
    }
    
    return render(request, 'business/admin/business_approval_list.html', context)

def get_chart_data():
    """Génère les données pour les graphiques"""
    
    # Données pour les 7 derniers jours
    dates = []
    business_counts = []
    transaction_amounts = []
    
    for i in range(7):
        date = timezone.now().date() - timedelta(days=i)
        dates.append(date.strftime('%d/%m'))
        
        # Nombre de nouveaux business
        count = BusinessLocation.objects.filter(
            created_at__date=date
        ).count()
        business_counts.append(count)
        
        # Montant des transactions
        amount = UserTransaction.objects.filter(
            created_at__date=date,
            status='COMPLETED'
        ).aggregate(total=Sum('amount'))['total'] or 0
        transaction_amounts.append(float(amount))
    
    # Inverser pour avoir l'ordre chronologique
    dates.reverse()
    business_counts.reverse()
    transaction_amounts.reverse()
    
    return {
        'dates': dates,
        'business_counts': business_counts,
        'transaction_amounts': transaction_amounts,
    }

@login_required
@user_passes_test(is_superuser)
def commission_dashboard(request):
    """Dashboard dédié aux commissions"""
    
    # Récupérer les paramètres de filtrage
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    business_type = request.GET.get('business_type')
    
    # Convertir les dates
    if start_date:
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
    if end_date:
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Obtenir les statistiques des commissions
    commission_stats = CommissionService.get_commission_statistics(start_date, end_date)
    
    # Filtrer les transactions de commission
    commission_transactions = UserTransaction.objects.filter(
        transaction_type='COMMISSION',
        status='COMPLETED'
    ).select_related('wallet__business_location__business')
    
    if start_date:
        commission_transactions = commission_transactions.filter(created_at__date__gte=start_date)
    if end_date:
        commission_transactions = commission_transactions.filter(created_at__date__lte=end_date)
    if business_type:
        commission_transactions = commission_transactions.filter(
            wallet__business_location__business_location_type=business_type
        )
    
    # Pagination
    paginator = Paginator(commission_transactions.order_by('-created_at'), 20)
    page = request.GET.get('page')
    commission_transactions = paginator.get_page(page)
    
    # Calculer le taux moyen de commission
    total_transactions = UserTransaction.objects.filter(
        transaction_type='PAYMENT',
        status='COMPLETED'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    commission_rate = 0
    if total_transactions > 0:
        commission_rate = (commission_stats['total_commission'] / total_transactions) * 100
    
    context = {
        'total_commission': commission_stats['total_commission'],
        'monthly_commission': commission_stats['monthly_commission'],
        'transaction_count': commission_stats['transaction_count'],
        'commission_rate': commission_rate,
        'commission_transactions': commission_transactions,
        'start_date': start_date,
        'end_date': end_date,
        'business_type': business_type,
    }
    
    return render(request, 'business/admin/commission_dashboard.html', context)

@login_required
@user_passes_test(is_superuser)
def api_dashboard_stats(request):
    """API pour les statistiques en temps réel"""
    
    # Statistiques rapides
    stats = {
        'total_businesses': BusinessLocation.objects.count(),
        'pending_approvals': BusinessLocation.objects.filter(is_verified=False).count(),
        'total_users': User.objects.count(),
        'active_businesses': BusinessLocation.objects.filter(is_active=True).count(),
    }
    
    return JsonResponse(stats) 