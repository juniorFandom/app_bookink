from django.urls import path
from .views import HomePageView, NavigationMenuView

app_name = 'home'

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('navigation/', NavigationMenuView.as_view(), name='navigation'),
]
