"""Global installation of the search field selector on every ModelAdmin."""

from __future__ import annotations

from django_admin_search_field.fields import (
    _search_field_var,
    build_search_field_choices,
    get_selected_search_field,
    resolve_search_fields,
)


def install_search_field_selector() -> None:
    """Enable the search field selector on EVERY ``ModelAdmin``.

    Instead of reclassifying every admin registered with ``@admin.register``,
    this patches the base ``ModelAdmin`` class itself (additive, idempotent
    monkey-patch):

    * ``get_search_fields`` now honours the ``sf`` GET parameter (restricts
      the search to a single field) — via
      :class:`django_admin_search_field.fields.SearchFieldSelectMixin`.
    * ``get_changelist_instance`` attaches the combobox options to the ``cl``
      object.
    * The ``sf`` parameter is registered in the changelist's
      ``IGNORED_PARAMS`` so it isn't treated as a list filter.

    Call this once, for example from your own app's ``AppConfig.ready()``:

        # myapp/apps.py
        class MyAppConfig(AppConfig):
            def ready(self):
                from django_admin_search_field import install_search_field_selector
                install_search_field_selector()

    Defensive: any failure here must never break the admin.
    """
    from django.contrib.admin.options import ModelAdmin

    if getattr(ModelAdmin, "_admin_search_field_installed", False):
        return

    # 1) 'sf' (or the configured override) must not be read as a list filter.
    from django.contrib.admin.views import main as admin_main

    search_field_var = _search_field_var()
    if search_field_var not in admin_main.IGNORED_PARAMS:
        admin_main.IGNORED_PARAMS = tuple(admin_main.IGNORED_PARAMS) + (search_field_var,)

    # 2) Wrap the original base-class methods, preserving them.
    original_get_search_fields = ModelAdmin.get_search_fields
    original_get_changelist_instance = ModelAdmin.get_changelist_instance

    def get_search_fields(self, request):
        original = original_get_search_fields(self, request)
        try:
            self._original_search_fields = tuple(original)
        except Exception:
            self._original_search_fields = original
        try:
            return resolve_search_fields(original, request)
        except Exception:
            return original

    def get_changelist_instance(self, request):
        cl = original_get_changelist_instance(self, request)
        try:
            cl.search_field_choices = build_search_field_choices(self, request)
            cl.search_field_selected = get_selected_search_field(request)
            cl.search_field_var = _search_field_var()
        except Exception:
            cl.search_field_choices = []
            cl.search_field_selected = ""
            cl.search_field_var = _search_field_var()
        return cl

    ModelAdmin.get_search_fields = get_search_fields
    ModelAdmin.get_changelist_instance = get_changelist_instance
    ModelAdmin._admin_search_field_installed = True
