"""Web views for user management."""
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib.messages.views import SuccessMessageMixin
from apps.rooms.models.room_booking import RoomBooking
from apps.vehicles.models.vehicle_booking import VehicleBooking
from apps.tours.models.tour_booking import TourBooking
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from datetime import datetime, timedelta

from ..forms import CustomUserCreationForm, CustomUserChangeForm
from ..models import User
from apps.business.models import Business


class RegisterView(SuccessMessageMixin, CreateView):
    """View for user registration."""
    template_name = 'users/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('users:profile')
    success_message = "Your account was created successfully"

    def form_valid(self, form):
        """Log the user in after successful registration."""
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class ProfileView(LoginRequiredMixin, DetailView):
    """View for displaying user profile."""
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        """Get the current user's profile."""
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_businesses'] = Business.objects.filter(owner=self.request.user)
        return context


class ProfileEditView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """View for editing user profile."""
    model = User
    form_class = CustomUserChangeForm
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:profile')
    success_message = "Your profile was updated successfully"

    def get_object(self, queryset=None):
        """Get the current user's profile."""
        return self.request.user


@login_required
def user_booking_list(request):
    user = request.user
    tab = request.GET.get('tab', 'room')
    page = request.GET.get('page', 1)
    bookings = []
    today = datetime.now().date()
    if tab == 'room':
        bookings = RoomBooking.objects.filter(customer=user).order_by('-created_at')
        for booking in bookings:
            already_paid = sum(
                t.amount for t in booking.transactions.filter(status='COMPLETED')
            )
            remaining_amount = booking.total_amount - already_paid
            booking.already_paid = already_paid
            booking.remaining_amount = remaining_amount
            booking.can_cancel = (booking.check_in_date - today) > timedelta(days=1)
    elif tab == 'vehicle':
        bookings = VehicleBooking.objects.filter(customer=user).order_by('-created_at')
    elif tab == 'tour':
        bookings = TourBooking.objects.filter(customer=user).order_by('-created_at')
    else:
        bookings = RoomBooking.objects.filter(customer=user).order_by('-created_at')
    paginator = Paginator(bookings, 10)
    bookings_page = paginator.get_page(page)
    return render(request, 'users/user_booking_list.html', {
        'bookings': bookings_page,
        'tab': tab,
        'paginator': paginator,
        'today': today,
    })
