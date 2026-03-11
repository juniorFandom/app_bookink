"""Guide app web views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    UpdateView,
    DetailView,
    ListView
)

from ..models import GuideProfile
from ..forms import GuideProfileForm
from ..services import (
    create_guide_profile,
    update_guide_profile
)


class GuideProfileCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """View for creating a guide profile."""
    model = GuideProfile
    form_class = GuideProfileForm
    template_name = 'guides/profile_create.html'
    success_url = reverse_lazy('guides:profile_detail')
    success_message = _('Your guide profile has been created successfully.')

    def form_valid(self, form):
        """Create guide profile and assign it to the current user."""
        profile = create_guide_profile(
            user=self.request.user,
            **form.cleaned_data
        )
        return redirect(self.success_url)


class GuideProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """View for updating a guide profile."""
    model = GuideProfile
    form_class = GuideProfileForm
    template_name = 'guides/profile_edit.html'
    success_url = reverse_lazy('guides:profile_detail')
    success_message = _('Your guide profile has been updated successfully.')

    def get_object(self, queryset=None):
        """Get the current user's guide profile."""
        return get_object_or_404(GuideProfile, user=self.request.user)

    def form_valid(self, form):
        """Update guide profile."""
        profile = update_guide_profile(
            profile=self.get_object(),
            data=form.cleaned_data
        )
        return super().form_valid(form)


class GuideProfileDetailView(LoginRequiredMixin, DetailView):
    """View for displaying a guide profile."""
    model = GuideProfile
    template_name = 'guides/profile_detail.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        """Get the current user's guide profile."""
        return get_object_or_404(GuideProfile, user=self.request.user)


class GuideProfileListView(ListView):
    """View for listing guide profiles."""
    model = GuideProfile
    template_name = 'guides/profile_list.html'
    context_object_name = 'profiles'
    paginate_by = 12

    def get_queryset(self):
        """Return verified guide profiles."""
        return self.model.objects.filter(is_verified=True)
