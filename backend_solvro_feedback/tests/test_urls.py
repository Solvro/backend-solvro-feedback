from django.test import TestCase
from django.urls import reverse, resolve

from backend_solvro_feedback.auth_views import (
    SolvroAdminLoginView,
    SolvroAdminAuthorizeView,
)


class UrlRoutingTestCase(TestCase):
    def test_solvro_login_url_resolves_to_login_view(self):
        url = reverse("solvro-login")
        self.assertEqual(url, "/admin/login/solvro/")

        resolved = resolve(url)
        self.assertEqual(resolved.func.view_class, SolvroAdminLoginView)

    def test_solvro_authorize_url_resolves_to_authorize_view(self):
        url = reverse("solvro-authorize")
        self.assertEqual(url, "/admin/authorize/")

        resolved = resolve(url)
        self.assertEqual(resolved.func.view_class, SolvroAdminAuthorizeView)

    def test_admin_url_resolves_to_django_admin(self):
        url = reverse("admin:index")
        self.assertEqual(url, "/admin/")
