from django.views.generic import TemplateView
from apps.tours.models import Tour
from apps.rooms.models import Room, RoomType

class HomePageView(TemplateView):
    template_name = 'home/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tours'] = Tour.objects.all()
        context['rooms'] = Room.objects.all()
        context['list'] = []
        return context

class NavigationMenuView(TemplateView):
    """Vue pour afficher le menu de navigation complet"""
    template_name = 'home/navigation_menu.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Menu de Navigation - Toutes les Routes'
        return context
