from django.db import models
from django.conf import settings

class TouristSiteCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class TouristSite(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(TouristSiteCategory, on_delete=models.SET_NULL, null=True, related_name='sites')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class TouristSiteImage(models.Model):
    site = models.ForeignKey(TouristSite, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='tourist_sites/')
    caption = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image de {self.site.name}" 