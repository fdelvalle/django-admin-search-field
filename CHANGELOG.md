# Changelog

## Unreleased

- Add a "favorite search field" star next to the combobox: the starred field
  is stored per model in the browser's `localStorage` and pre-selected when
  the changelist is opened without an explicit `sf` or an ongoing search.
- Ship `static/django_admin_search_field/js/search_field.js` in the package
  data (loaded automatically by the bundled `admin/search_form.html`).

## 0.1.1

- Fix: `SEARCH_FIELD_VAR` (the default GET parameter name) is now reexported
  from the top-level `django_admin_search_field` package, not just from
  `django_admin_search_field.fields`.
- Add `get_search_field_var()` (public) as the setting-aware accessor for the
  GET parameter name, replacing the private `_search_field_var()`.

## 0.1.0

- Initial extraction from a private Django project's admin customizations
  into a standalone, generic package: field-scoped search combobox for the
  Django admin changelist (`SearchFieldSelectMixin`,
  `install_search_field_selector`), bundled template and CSS override.
