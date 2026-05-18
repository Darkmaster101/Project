from django.contrib import admin
from .models import AppSession


@admin.register(AppSession)
class AppSessionAdmin(admin.ModelAdmin):
    list_display  = ("id", "username", "hostname", "opened_at", "closed_at", "duration_seconds")
    list_filter   = ("username", "hostname")
    readonly_fields = ("opened_at",)
    ordering      = ("-opened_at",)
