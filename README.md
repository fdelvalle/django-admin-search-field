# django-admin-search-field

[![Latest on Django Packages](https://img.shields.io/badge/PyPI-django-admin-search-field-tags-8c3c26.svg)](https://djangopackages.org/packages/p/django-admin-search-field/)

A per-field search selector for the Django admin changelist.

By default, the Django admin searches the submitted term across **every**
field listed in a `ModelAdmin.search_fields` (joined with `OR`). On tables
with many fields, several relations, or large row counts, that makes the
search slow — and there is no built-in way to search a single field instead.

This package adds a small combobox next to the search box, letting the user
restrict the search to **one** field — or keep "All fields" for the native
behaviour.

## Features

- Adds a `<select>` next to the changelist search box with one option per
  `search_fields` entry, using a friendly label (`verbose_name`, following
  relations, e.g. `author__name` → "Author › Name").
- Restricts the actual search query to the chosen field via the `sf` GET
  parameter (name configurable).
- Works globally, for every registered `ModelAdmin`, via a single opt-in
  call — no need to touch each `admin.py`.
- Also available as an explicit mixin (`SearchFieldSelectMixin`) if you'd
  rather opt in per `ModelAdmin`.
- Defensive by design: any unexpected failure falls back to Django's native
  search behaviour instead of breaking the admin page.
- Ships a template override (`admin/search_form.html`) and a small,
  dependency-free CSS file that follows the admin's own light/dark theme
  variables.

## Installation

```bash
pip install django-admin-search-field
```

Add the app to `INSTALLED_APPS`, **before** `django.contrib.admin` (required
so the bundled `admin/search_form.html` overrides Django's default template
via the `app_directories` template loader):

```python
INSTALLED_APPS = [
    "django_admin_search_field",
    "django.contrib.admin",
    ...
]
```

Enable the selector once, globally — e.g. from your own app's
`AppConfig.ready()`:

```python
# myapp/apps.py
from django.apps import AppConfig


class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        from django_admin_search_field import install_search_field_selector

        install_search_field_selector()
```

(Optional) include the bundled CSS in your `admin/base_site.html` (or
wherever you already extend the admin base template):

```html
{% load static %}
<link rel="stylesheet" href="{% static 'django_admin_search_field/css/search_field.css' %}">
```

That's it — every `ModelAdmin` with `search_fields` configured now shows the
field selector.

## Usage without the global monkey-patch

If you'd rather enable this on a single `ModelAdmin`, skip
`install_search_field_selector()` and use the mixin instead:

```python
from django.contrib import admin
from django_admin_search_field import SearchFieldSelectMixin

from myapp.models import Book


@admin.register(Book)
class BookAdmin(SearchFieldSelectMixin, admin.ModelAdmin):
    search_fields = ["title", "isbn", "author__name"]
```

In this mode you're responsible for including the CSS/template yourself,
and you don't need to add `django_admin_search_field` to `INSTALLED_APPS` —
only the Python mixin is used.

## Configuration

| Setting | Default | Description |
|---|---|---|
| `ADMIN_SEARCH_FIELD_VAR` | `"sf"` | Name of the GET parameter used to carry the chosen field. Override it if `sf` collides with something else in your project. |

## How it works

- `resolve_search_fields()` restricts `search_fields` to the field selected
  via the `sf` GET parameter — or returns the original list unchanged when
  `sf` is empty ("All fields") or points to a field that isn't configured.
- `sf` is registered in the changelist's `IGNORED_PARAMS`, so it's never
  misread as a list filter (which would otherwise raise
  `IncorrectLookupParameters`).
- The template only receives the `cl` (ChangeList) object, so the combobox
  data is attached directly to it: `cl.search_field_choices`,
  `cl.search_field_selected`, `cl.search_field_var`.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Compatibility

- Python 3.10+
- Django 4.2+

## License

MIT — see [LICENSE](LICENSE).
