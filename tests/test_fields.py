"""Tests for django_admin_search_field.fields.

Covers:
* ``strip_search_prefix`` / ``label_for_search_field`` (friendly labels).
* ``resolve_search_fields`` (restricting search to the chosen field).
* ``build_search_field_choices`` (options exposed to the template).
"""

from unittest.mock import MagicMock

from django.test import RequestFactory, SimpleTestCase

from django_admin_search_field.fields import (
    build_search_field_choices,
    label_for_search_field,
    resolve_search_fields,
    strip_search_prefix,
)
from tests.testapp.models import Book


def _request(sf=None):
    factory = RequestFactory()
    data = {}
    if sf is not None:
        data["sf"] = sf
    return factory.get("/admin/", data)


class StripPrefixTests(SimpleTestCase):
    def test_strips_known_prefixes(self):
        self.assertEqual(strip_search_prefix("^title"), "title")
        self.assertEqual(strip_search_prefix("=isbn"), "isbn")
        self.assertEqual(strip_search_prefix("@title"), "title")

    def test_no_prefix_unchanged(self):
        self.assertEqual(strip_search_prefix("author__name"), "author__name")


class LabelTests(SimpleTestCase):
    def test_label_uses_verbose_name(self):
        # verbose_name="ISBN" is title-cased by .capitalize(), same as any
        # other field label in this module.
        label = label_for_search_field(Book, "isbn")
        self.assertEqual(label, "Isbn")

    def test_label_follows_relation(self):
        label = label_for_search_field(Book, "author__name")
        self.assertIn("›", label)

    def test_label_strips_prefix(self):
        self.assertEqual(
            label_for_search_field(Book, "=title"),
            label_for_search_field(Book, "title"),
        )

    def test_label_fallback_for_unknown_field(self):
        label = label_for_search_field(Book, "does_not_exist")
        self.assertEqual(label, "Does not exist")


class ResolveSearchFieldsTests(SimpleTestCase):
    def setUp(self):
        self.fields = ("title", "isbn", "author__name")

    def test_all_when_no_sf(self):
        self.assertEqual(resolve_search_fields(self.fields, _request()), self.fields)
        self.assertEqual(resolve_search_fields(self.fields, _request("")), self.fields)

    def test_restricts_to_selected(self):
        out = resolve_search_fields(self.fields, _request("title"))
        self.assertEqual(out, ("title",))

    def test_ignores_unknown_field(self):
        out = resolve_search_fields(self.fields, _request("hacker__field"))
        self.assertEqual(out, self.fields)


class BuildChoicesTests(SimpleTestCase):
    def test_choices_include_all_fields_with_selection(self):
        admin_obj = MagicMock()
        admin_obj.model = Book
        admin_obj._original_search_fields = ("title", "isbn", "author__name")
        choices = build_search_field_choices(admin_obj, _request("isbn"))
        values = [c["value"] for c in choices]
        self.assertEqual(values, ["title", "isbn", "author__name"])
        selected = [c["value"] for c in choices if c["selected"]]
        self.assertEqual(selected, ["isbn"])
        for c in choices:
            self.assertTrue(c["label"])
