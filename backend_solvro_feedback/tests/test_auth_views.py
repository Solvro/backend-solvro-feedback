from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User

# Note: Some end-to-end tests may fail if the application is not yet
# registered in Solvro Auth (https://auth.solvro.pl)
from django.test import RequestFactory, TestCase

from backend_solvro_feedback.auth_views import (
    SolvroAdminAuthorizeView,
    SolvroAdminLoginView,
)


class SolvroAdminLoginViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("backend_solvro_feedback.auth_views.oauth")
    def test_login_returns_oauth_redirect(self, mock_oauth):
        request = self.factory.get("/admin/login/solvro/")

        mock_client = MagicMock()
        mock_oauth.create_client.return_value = mock_client

        response = SolvroAdminLoginView.as_view()(request)

        mock_oauth.create_client.assert_called_once_with("solvro-auth")
        mock_client.authorize_redirect.assert_called_once()
        self.assertEqual(response, mock_client.authorize_redirect.return_value)


class SolvroAdminAuthorizeViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("backend_solvro_feedback.auth_views.oauth")
    def test_authorize_token_failure_returns_bad_request(self, mock_oauth):
        request = self.factory.get("/admin/authorize/")

        mock_client = MagicMock()
        mock_client.authorize_access_token.side_effect = Exception("Token error")
        mock_oauth.create_client.return_value = mock_client

        response = SolvroAdminAuthorizeView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"Failed to obtain access token.")

    @patch("backend_solvro_feedback.auth_views.oauth")
    def test_authorize_userinfo_failure_returns_bad_request(self, mock_oauth):
        request = self.factory.get("/admin/authorize/")

        mock_client = MagicMock()
        mock_client.authorize_access_token.return_value = {"access_token": "token"}
        mock_client.get.side_effect = Exception("Userinfo error")
        mock_oauth.create_client.return_value = mock_client

        response = SolvroAdminAuthorizeView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"Failed to retrieve user profile.")

    @patch("backend_solvro_feedback.auth_views.oauth")
    def test_authorize_missing_email_returns_bad_request(self, mock_oauth):
        request = self.factory.get("/admin/authorize/")

        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.authorize_access_token.return_value = {"access_token": "token"}
        mock_client.get.return_value = mock_response
        mock_oauth.create_client.return_value = mock_client

        response = SolvroAdminAuthorizeView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"Missing email in user profile.")

    @patch("backend_solvro_feedback.auth_views.login")
    @patch("backend_solvro_feedback.auth_views.oauth")
    def test_new_user_created_with_unusable_password(self, mock_oauth, mock_login):
        request = self.factory.get("/admin/authorize/")

        mock_response = MagicMock()
        mock_response.json.return_value = {"email": "test@solvro.pl"}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.authorize_access_token.return_value = {"access_token": "token"}
        mock_client.get.return_value = mock_response
        mock_oauth.create_client.return_value = mock_client

        response = SolvroAdminAuthorizeView.as_view()(request)

        user = User.objects.get(username="test@solvro.pl")
        self.assertFalse(user.has_usable_password())
        mock_login.assert_called_once()
        self.assertEqual(response.url, "/admin/")

    @patch("backend_solvro_feedback.auth_views.login")
    @patch("backend_solvro_feedback.auth_views.oauth")
    def test_existing_user_password_preserved(self, mock_oauth, mock_login):
        user = User.objects.create_user(
            username="existing@solvro.pl",
            email="existing@solvro.pl",
            password="existingpassword",
        )

        request = self.factory.get("/admin/authorize/")

        mock_response = MagicMock()
        mock_response.json.return_value = {"email": "existing@solvro.pl"}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.authorize_access_token.return_value = {"access_token": "token"}
        mock_client.get.return_value = mock_response
        mock_oauth.create_client.return_value = mock_client

        response = SolvroAdminAuthorizeView.as_view()(request)

        user.refresh_from_db()
        self.assertTrue(user.has_usable_password())
        mock_login.assert_called_once()
        self.assertEqual(response.url, "/admin/")

    @patch("backend_solvro_feedback.auth_views.login")
    @patch("backend_solvro_feedback.auth_views.oauth")
    def test_successful_login_redirects_to_admin(self, mock_oauth, mock_login):
        request = self.factory.get("/admin/authorize/")

        mock_response = MagicMock()
        mock_response.json.return_value = {"email": "new@solvro.pl"}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.authorize_access_token.return_value = {"access_token": "token"}
        mock_client.get.return_value = mock_response
        mock_oauth.create_client.return_value = mock_client

        response = SolvroAdminAuthorizeView.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/")
