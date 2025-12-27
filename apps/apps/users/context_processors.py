def notif_count(request):
    """
    Context processor pour ajouter le nombre de notifications non lues
    et les dernières notifications à tous les templates.
    """
    notif_count = 0
    recent_notifications = []
    
    if request.user.is_authenticated:
        notif_count = request.user.notifications.filter(is_read=False).count()
        recent_notifications = request.user.notifications.order_by('-date')[:10]
    
    return {
        'notif_count': notif_count,
        'recent_notifications': recent_notifications
    } 