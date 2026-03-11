from django.contrib import admin
from apps.tourist_sites.models import TouristSite, TouristSiteCategory, TouristSiteImage, ZoneDangereuse, ZoneDangereuseVote, Notification


@admin.register(TouristSiteCategory)
class TouristSiteCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']
    ordering = ['name']


class TouristSiteImageInline(admin.TabularInline):
    model = TouristSiteImage
    extra = 1
    fields = ['image', 'caption', 'is_primary']


@admin.register(TouristSite)
class TouristSiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'latitude', 'longitude', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    inlines = [TouristSiteImageInline]
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'category', 'is_active')
        }),
        ('Géolocalisation', {
            'fields': ('latitude', 'longitude')
        }),
    )


@admin.register(ZoneDangereuse)
class ZoneDangereuseAdmin(admin.ModelAdmin):
    list_display = ['nom_zone', 'type_danger', 'statut', 'date_signalement', 'guide_rapporteur', 'site']
    list_filter = ['statut', 'type_danger', 'date_signalement', 'site']
    search_fields = ['nom_zone', 'description_danger']
    ordering = ['-date_signalement']


@admin.register(ZoneDangereuseVote)
class ZoneDangereuseVoteAdmin(admin.ModelAdmin):
    list_display = ['zone', 'utilisateur', 'is_like', 'date_vote']
    list_filter = ['is_like', 'date_vote']
    search_fields = ['zone__nom_zone', 'utilisateur__username']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['destinataire', 'message', 'url', 'is_read', 'date']
    list_filter = ['is_read', 'date']
    search_fields = ['destinataire__username', 'message'] 