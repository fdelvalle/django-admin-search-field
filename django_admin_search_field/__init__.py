"""A per-field search selector for the Django admin changelist.

By default, the Django admin searches the submitted term across every field
in ``search_fields`` (joined with OR). On large tables with many fields and
relations, that makes search slow. This package adds a combobox next to the
search box so users can restrict a search to a single field.

Installation
------------
1. ``pip install django-admin-search-field``

2. Add ``"django_admin_search_field"`` to ``INSTALLED_APPS``, **before**
   ``"django.contrib.admin"`` (required so the bundled
   ``admin/search_form.html`` template overrides Django's default one)::

    INSTALLED_APPS = [
        "django_admin_search_field",
        "django.contrib.admin",
        ...
    ]

3. Enable the selector globally, once — e.g. in your own app's
   ``AppConfig.ready()``::

    from django_admin_search_field import install_search_field_selector

    class MyAppConfig(AppConfig):
        def ready(self):
            install_search_field_selector()

4. (Optional) include the bundled CSS in your ``admin/base_site.html``::

    {% load static %}
    <link rel="stylesheet" href="{% static 'django_admin_search_field/css/search_field.css' %}">

Explicit, per-admin use (no global monkey-patch)
-------------------------------------------------
To enable the selector on a single ``ModelAdmin`` only, use the mixin::

    from django_admin_search_field import SearchFieldSelectMixin

    @admin.register(MyModel)
    class MyModelAdmin(SearchFieldSelectMixin, admin.ModelAdmin):
        search_fields = ["name", "owner__email"]
"""

from __future__ import annotations

from django_admin_search_field.fields import (
    SearchFieldSelectMixin,
    build_search_field_choices,
    get_selected_search_field,
    label_for_search_field,
    resolve_search_fields,
    strip_search_prefix,
)
from django_admin_search_field.install import install_search_field_selector

__version__ = "0.1.0"

default_app_config = "django_admin_search_field.apps.AdminSearchFieldConfig"

__all__ = [
    "SearchFieldSelectMixin",
    "build_search_field_choices",
    "get_selected_search_field",
    "install_search_field_selector",
    "label_for_search_field",
    "resolve_search_fields",
    "strip_search_prefix",
]
