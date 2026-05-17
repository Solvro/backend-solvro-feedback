from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
class TestSolvroAuthUrls:
    def test_solvro_login_url_exists(self):
        url = reverse("solvro-login")
        assert url == "/admin/login/solvro/"

    def test_solvro_authorize_url_exists(self):
        url = reverse("solvro-authorize")
        assert url == "/admin/authorize/"


@pytest.mark.django_db
class TestSolvroAdminLoginView:
    def test_login_view_exists(self):
        from backend_solvro_feedback.auth_views import SolvroAdminLoginView

        assert SolvroAdminLoginView is not None

    def test_login_view_uses_oauth(self):
        from backend_solvro_feedback.auth_views import SolvroAdminLoginView

        assert hasattr(SolvroAdminLoginView, "get")


@pytest.mark.django_db
class TestSolvroAdminAuthorizeView:
    @patch("backend_solvro_feedback.auth_views.oauth.create_client")
    def test_authorize_success(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.authorize_access_token.return_value = {"access_token": "token"}

        mock_response = MagicMock()
        mock_response.json.return_value = {"email": "test@solvro.pl"}
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response
        mock_create_client.return_value = mock_client

        client = Client()
        response = client.get("/admin/authorize/?code=test-code")

        assert response.status_code == 302
        assert response.url == "/admin/"
        assert User.objects.filter(username="test@solvro.pl").exists()

    @patch("backend_solvro_feedback.auth_views.oauth.create_client")
    def test_authorize_creates_user(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.authorize_access_token.return_value = {"access_token": "token"}

        mock_response = MagicMock()
        mock_response.json.return_value = {"email": "newuser@solvro.pl"}
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response
        mock_create_client.return_value = mock_client

        client = Client()
        client.get("/admin/authorize/?code=test-code")

        user = User.objects.get(username="newuser@solvro.pl")
        assert user.email == "newuser@solvro.pl"
        assert not user.has_usable_password()

    @patch("backend_solvro_feedback.auth_views.oauth.create_client")
    def test_authorize_existing_user(self, mock_create_client):
        User.objects.create_user(
            username="existing@solvro.pl", email="existing@solvro.pl"
        )

        mock_client = MagicMock()
        mock_client.authorize_access_token.return_value = {"access_token": "token"}

        mock_response = MagicMock()
        mock_response.json.return_value = {"email": "existing@solvro.pl"}
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response
        mock_create_client.return_value = mock_client

        client = Client()
        client.get("/admin/authorize/?code=test-code")

        assert User.objects.filter(username="existing@solvro.pl").count() == 1

    @patch("backend_solvro_feedback.auth_views.oauth.create_client")
    def test_authorize_missing_email(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.authorize_access_token.return_value = {"access_token": "token"}

        mock_response = MagicMock()
        mock_response.json.return_value = {"name": "No Email"}
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response
        mock_create_client.return_value = mock_client

        client = Client()
        response = client.get("/admin/authorize/?code=test-code")

        assert response.status_code == 400
        assert b"Missing email" in response.content

    @patch("backend_solvro_feedback.auth_views.oauth.create_client")
    def test_authorize_token_error(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.authorize_access_token.side_effect = Exception("Token error")
        mock_create_client.return_value = mock_client

        client = Client()
        response = client.get("/admin/authorize/?code=test-code")

        assert response.status_code == 400
        assert b"Failed to obtain access token" in response.content

    @patch("backend_solvro_feedback.auth_views.oauth.create_client")
    def test_authorize_profile_error(self, mock_create_client):
        mock_client = MagicMock()
        mock_client.authorize_access_token.return_value = {"access_token": "token"}

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("Profile error")
        mock_client.get.return_value = mock_response
        mock_create_client.return_value = mock_client

        client = Client()
        response = client.get("/admin/authorize/?code=test-code")

        assert response.status_code == 400
        assert b"Failed to retrieve user profile" in response.content
