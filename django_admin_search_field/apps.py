from __future__ import annotations

from django.apps import AppConfig


class AdminSearchFieldConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_admin_search_field"
    label = "admin_search_field"
    verbose_name = "Admin Search Field Selector"
