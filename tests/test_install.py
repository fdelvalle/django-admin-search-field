"""Integration tests for django_admin_search_field.install.

Uses the real BookAdmin (registered in tests/testapp/admin.py) with the
global monkey-patch applied, plus a template-resolution check confirming the
packaged admin/search_form.html actually overrides Django's default one.
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.template import loader
from django.test import RequestFactory, TestCase

from django_admin_search_field.install import install_search_field_selector
from tests.testapp.models import Book


def _request(sf=None):
    factory = RequestFactory()
    data = {}
    if sf is not None:
        data["sf"] = sf
    return factory.get("/admin/testapp/book/", data)


class InstallIdempotencyTests(TestCase):
    def test_install_is_idempotent(self):
        install_search_field_selector()
        patched_get_search_fields = admin.ModelAdmin.get_search_fields
        install_search_field_selector()
        self.assertIs(admin.ModelAdmin.get_search_fields, patched_get_search_fields)


class ModelAdminIntegrationTests(TestCase):
    def setUp(self):
        install_search_field_selector()
        self.model_admin = admin.site._registry[Book]

    def test_get_search_fields_all_by_default(self):
        req = _request()
        fields = self.model_admin.get_search_fields(req)
        self.assertIn("title", fields)
        self.assertIn("author__name", fields)

    def test_get_search_fields_restricted_by_sf(self):
        req = _request("title")
        fields = self.model_admin.get_search_fields(req)
        self.assertEqual(tuple(fields), ("title",))
        # The full list stays available for the template.
        self.assertIn("author__name", self.model_admin._original_search_fields)

    def test_changelist_instance_exposes_choices(self):
        User = get_user_model()
        user = User.objects.create_superuser(username="admin_sf", email="a@b.co", password="x")
        req = _request("title")
        req.user = user
        cl = self.model_admin.get_changelist_instance(req)
        self.assertTrue(getattr(cl, "search_field_choices", None))
        self.assertEqual(cl.search_field_selected, "title")
        self.assertEqual(cl.search_field_var, "sf")


class TemplateOverrideTests(TestCase):
    def test_packaged_template_wins_over_django_default(self):
        template = loader.get_template("admin/search_form.html")
        origin_name = template.template.origin.name
        self.assertIn("django_admin_search_field", origin_name)


class ChangelistRenderTests(TestCase):
    """Full-stack check: hit the real changelist view and inspect the HTML."""

    def setUp(self):
        install_search_field_selector()
        User = get_user_model()
        self.user = User.objects.create_superuser(username="root", email="root@example.com", password="x")
        self.client.force_login(self.user)

    def test_combobox_rendered_with_all_options(self):
        response = self.client.get("/admin/testapp/book/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('id="search-field-select"', html)
        self.assertIn(">Title<", html)
        self.assertIn(">Author › Name<", html)

    def test_selected_field_marked_in_combobox(self):
        response = self.client.get("/admin/testapp/book/", {"sf": "title"})
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('value="title" selected', html)
