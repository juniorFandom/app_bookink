# Register your models here.
from django.contrib import admin
from .models import User, UserRole, Role

admin.site.register(User)
admin.site.register(UserRole)
admin.site.register(Role)

