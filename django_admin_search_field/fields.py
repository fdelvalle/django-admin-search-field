"""Search field selector logic for the Django admin.

By default, the Django admin searches the submitted term across every field
listed in ``search_fields`` (joined with OR). On large tables with many
fields and relations, this makes search slow.

This module adds a combobox next to the search box, letting the user pick a
**single** field to search — or "All fields" to keep the native behaviour.

How it works
-------------
* The bundled ``admin/search_form.html`` template renders a ``<select>`` with
  one option per entry in ``search_fields`` (with a friendly label for each
  field) plus an "All fields" option. The chosen field is submitted via the
  ``sf`` GET parameter (configurable, see ``SEARCH_FIELD_VAR`` below).
* ``resolve_search_fields`` restricts the search to the chosen field when
  ``sf`` is valid; otherwise it returns the original fields unchanged.
* The ``sf`` parameter must be registered in the changelist's
  ``IGNORED_PARAMS`` so it isn't treated as a list filter — this is handled by
  :func:`django_admin_search_field.install.install_search_field_selector`.

The feature is enabled globally by ``install_search_field_selector`` (an
additive monkey-patch on the base ``ModelAdmin`` class). Everything here is
defensive: any failure falls back to native admin behaviour.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db.models.constants import LOOKUP_SEP

# Lookup prefixes accepted by Django in ``search_fields``.
_LOOKUP_PREFIXES = ("^", "=", "@")


def _search_field_var() -> str:
    """Name of the GET parameter carrying the chosen field.

    Override with ``ADMIN_SEARCH_FIELD_VAR`` in your Django settings if ``sf``
    collides with something else in your project.
    """
    return getattr(settings, "ADMIN_SEARCH_FIELD_VAR", "sf")


# Kept as a module-level constant for convenience/backwards compatibility.
# Prefer calling ``_search_field_var()`` internally so overrides via settings
# take effect even after this module has been imported.
SEARCH_FIELD_VAR = "sf"


def strip_search_prefix(field: str) -> str:
    """Strip the lookup prefixes (``^``, ``=``, ``@``) from a search_field entry."""
    field = str(field)
    while field and field[0] in _LOOKUP_PREFIXES:
        field = field[1:]
    return field


def label_for_search_field(model, field: str) -> str:
    """Derive a friendly label for a ``search_fields`` entry.

    Tries to use the field's ``verbose_name`` (following relations, e.g.
    ``owner__name``). Falls back to a label derived from the raw field name
    (``owner__name`` -> "Owner name") when it can't be resolved.
    """
    clean = strip_search_prefix(field)
    parts = clean.split(LOOKUP_SEP)

    opts = getattr(model, "_meta", None)
    labels: list[str] = []
    resolved = True

    for part in parts:
        if opts is None:
            resolved = False
            break
        name = opts.pk.name if part == "pk" else part
        try:
            model_field = opts.get_field(name)
        except (FieldDoesNotExist, AttributeError):
            resolved = False
            break

        verbose = getattr(model_field, "verbose_name", None) or name
        labels.append(str(verbose).strip().capitalize())

        # Follow the relation, if any, to resolve the next part.
        related = getattr(model_field, "related_model", None)
        opts = getattr(related, "_meta", None) if related else None

    if resolved and labels:
        return " › ".join(labels)

    # Fallback: build a label from the raw name.
    return clean.replace(LOOKUP_SEP, " ").replace("_", " ").strip().capitalize()


def get_selected_search_field(request) -> str:
    """Return the field chosen in the GET params, or ``""`` for "All fields"."""
    try:
        return (request.GET.get(_search_field_var()) or "").strip()
    except Exception:
        return ""


def resolve_search_fields(original_search_fields, request):
    """Restrict ``search_fields`` to the field chosen in the combobox.

    If the selector is empty ("All fields") or points to a field that isn't
    configured (e.g. an arbitrary value from the URL), the original list is
    returned unchanged — keeping native admin behaviour.
    """
    selected = get_selected_search_field(request)
    if not selected:
        return original_search_fields
    if selected in {str(f) for f in (original_search_fields or ())}:
        return (selected,)
    return original_search_fields


def build_search_field_choices(model_admin, request) -> list[dict]:
    """Build the combobox options from ``search_fields``.

    Returns a list of dicts ``{"value", "label", "selected"}``. Does not
    include the "All fields" option (the template handles that). Returns an
    empty list if the admin has no ``search_fields``.

    Uses the FULL list of fields (stashed on ``_original_search_fields`` by
    ``get_search_fields``) so every option is always listed, even once the
    search is already restricted to a single field.
    """
    search_fields = getattr(model_admin, "_original_search_fields", None)
    if search_fields is None:
        try:
            search_fields = model_admin.get_search_fields(request)
        except Exception:
            search_fields = getattr(model_admin, "search_fields", None) or ()

    selected = get_selected_search_field(request)
    model = getattr(model_admin, "model", None)

    choices: list[dict] = []
    seen: set[str] = set()
    for field in search_fields or ():
        value = str(field)
        if value in seen:
            continue
        seen.add(value)
        choices.append(
            {
                "value": value,
                "label": label_for_search_field(model, value),
                "selected": value == selected,
            }
        )
    return choices


class SearchFieldSelectMixin:
    """Restrict search to the field chosen in the combobox (``sf`` param).

    ``install_search_field_selector`` applies this behaviour globally via a
    monkey-patch (every ``ModelAdmin`` gets the selector). This mixin is also
    available for explicit use/tests, or to enable the feature on a single
    admin class without the global monkey-patch.
    """

    def get_search_fields(self, request):
        original = super().get_search_fields(request)
        # Stash the full list so the template can list every option, even
        # when the search is currently restricted to one field.
        try:
            self._original_search_fields = tuple(original)
        except Exception:
            self._original_search_fields = original
        return resolve_search_fields(original, request)

    def get_changelist_instance(self, request):
        """Attach the selector's data to the ChangeList instance.

        The ``admin/search_form.html`` template only receives the ``cl``
        object (the ``search_form`` inclusion tag builds its context from
        it), so we expose the options there: ``cl.search_field_choices``,
        ``cl.search_field_selected`` and ``cl.search_field_var``.
        """
        cl = super().get_changelist_instance(request)
        try:
            cl.search_field_choices = build_search_field_choices(self, request)
            cl.search_field_selected = get_selected_search_field(request)
            cl.search_field_var = _search_field_var()
        except Exception:
            cl.search_field_choices = []
            cl.search_field_selected = ""
            cl.search_field_var = _search_field_var()
        return cl
