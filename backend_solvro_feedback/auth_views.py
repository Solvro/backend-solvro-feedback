from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.views import View
from django.urls import reverse
from django.http import HttpResponseBadRequest
import logging

from backend_solvro_feedback.settings import oauth

logger = logging.getLogger(__name__)


class SolvroAdminLoginView(View):
    """Initiate Solvro OAuth login flow for Django Admin."""

    def get(self, request):
        callback_url = request.build_absolute_uri(reverse("solvro-authorize"))
        client = oauth.create_client("solvro-auth")
        return client.authorize_redirect(request, callback_url)


class SolvroAdminAuthorizeView(View):
    """Solvro OAuth callback for Django Admin."""

    def get(self, request):
        try:
            client = oauth.create_client("solvro-auth")
            token = client.authorize_access_token(request)
        except Exception as e:
            logger.error(
                f"Failed to obtain Solvro auth access token: {e}", exc_info=True
            )
            return HttpResponseBadRequest("Failed to obtain access token.")

        try:
            resp = client.get(
                "https://auth.solvro.pl/realms/solvro/protocol/openid-connect/userinfo",
                token=token,
            )
            resp.raise_for_status()
            profile = resp.json()
        except Exception as e:
            logger.error(f"Failed to retrieve Solvro user profile: {e}", exc_info=True)
            return HttpResponseBadRequest("Failed to retrieve user profile.")

        email = profile.get("email")
        if not email:
            logger.error("Solvro user profile missing email.")
            return HttpResponseBadRequest("Missing email in user profile.")

        # Ensure the user exists and has admin permissions
        user, created = User.objects.get_or_create(
            username=email, defaults={"email": email}
        )

        # Grant staff and superuser permissions if not already granted
        if not user.is_staff or not user.is_superuser:
            user.is_staff = True
            user.is_superuser = True
            user.save()

        # Log the user in
        login(request, user)

        # Redirect to the admin page
        return redirect("admin:index")
