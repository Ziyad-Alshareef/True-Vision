from django.contrib import admin

# Register your models here.

from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Analysis

admin.site.register(CustomUser, UserAdmin)
admin.site.register(Analysis)