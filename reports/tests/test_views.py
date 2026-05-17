import base64
import uuid

from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from reports.models import Application, Issue, IssueAttachment

TEST_REST_FRAMEWORK_NO_THROTTLE = {
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "public_report_burst": "1000/min",
        "public_report_sustained": "1000/min",
    },
}

TEST_REST_FRAMEWORK_THROTTLE_STRICT = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "public_report_burst": "2/min",
        "public_report_sustained": "2/min",
    },
}


def _setup_throttle_rates():
    from rest_framework.settings import api_settings

    from reports.views import (
        PublicReportBurstRateThrottle,
        PublicReportSustainedRateThrottle,
    )

    PublicReportBurstRateThrottle.THROTTLE_RATES = dict(
        api_settings.DEFAULT_THROTTLE_RATES
    )
    PublicReportSustainedRateThrottle.THROTTLE_RATES = dict(
        api_settings.DEFAULT_THROTTLE_RATES
    )


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK_NO_THROTTLE)
class TestPublicReportCreateView(APITestCase):
    def setUp(self):
        cache.clear()
        _setup_throttle_rates()
        self.application = Application.objects.create(
            name="Test App",
            repo_url="https://github.com/test/repo",
            is_active=True,
        )
        self.url = reverse("report-create", kwargs={"app_id": self.application.id})
        self.valid_b64 = base64.b64encode(b"fake-image-data").decode("utf-8")

    def _payload(self, attachments=None):
        return {
            "title": "App crash",
            "description": "The application crashes on startup every time.",
            "diagnostics": {"os": "Android", "version": "12"},
            "attachments": attachments or [],
        }

    def test_create_report_success(self):
        response = self.client.post(self.url, self._payload(), format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "NEW"
        assert response.data["application_id"] == str(self.application.id)
        assert Issue.objects.count() == 1

    def test_create_report_with_attachment(self):
        payload = self._payload(
            attachments=[
                {
                    "filename": "screen.png",
                    "content_type": "image/png",
                    "content_base64": self.valid_b64,
                }
            ]
        )
        response = self.client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert IssueAttachment.objects.count() == 1
        attachment = IssueAttachment.objects.first()
        assert attachment.filename == "screen.png"
        assert attachment.content_type == "image/png"
        assert attachment.size > 0

    def test_create_report_unknown_app(self):
        url = reverse("report-create", kwargs={"app_id": uuid.uuid4()})
        response = self.client.post(url, self._payload(), format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Issue.objects.count() == 0

    def test_create_report_inactive_app(self):
        app = Application.objects.create(
            name="Inactive App",
            repo_url="https://github.com/test/repo",
            is_active=False,
        )
        url = reverse("report-create", kwargs={"app_id": app.id})
        response = self.client.post(url, self._payload(), format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_report_title_too_short(self):
        payload = self._payload()
        payload["title"] = "Ab"
        response = self.client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_report_description_too_short(self):
        payload = self._payload()
        payload["description"] = "Short"
        response = self.client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_report_too_many_attachments(self):
        attachments = [
            {
                "filename": f"file{i}.png",
                "content_type": "image/png",
                "content_base64": self.valid_b64,
            }
            for i in range(6)
        ]
        payload = self._payload(attachments=attachments)
        response = self.client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Issue.objects.count() == 0

    def test_create_report_invalid_base64(self):
        payload = self._payload(
            attachments=[
                {
                    "filename": "bad.png",
                    "content_type": "image/png",
                    "content_base64": "!!!not-valid-base64!!!",
                }
            ]
        )
        response = self.client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_report_filename_sanitized(self):
        payload = self._payload(
            attachments=[
                {
                    "filename": "../../../etc/passwd!@#.png",
                    "content_type": "image/png",
                    "content_base64": self.valid_b64,
                }
            ]
        )
        response = self.client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        attachment = IssueAttachment.objects.first()
        assert attachment.filename == "passwd.png"

    def test_create_report_disallowed_content_type(self):
        payload = self._payload(
            attachments=[
                {
                    "filename": "malware.exe",
                    "content_type": "application/x-msdownload",
                    "content_base64": self.valid_b64,
                }
            ]
        )
        response = self.client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_report_s3_key_generated(self):
        payload = self._payload(
            attachments=[
                {
                    "filename": "test.png",
                    "content_type": "image/png",
                    "content_base64": self.valid_b64,
                }
            ]
        )
        response = self.client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        attachment = IssueAttachment.objects.first()
        assert attachment.s3_key.startswith("issues/")
        assert "test.png" in attachment.s3_key


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK_THROTTLE_STRICT)
class TestReportThrottling(APITestCase):
    def setUp(self):
        cache.clear()
        _setup_throttle_rates()
        self.application = Application.objects.create(
            name="Throttle App",
            repo_url="https://github.com/test/repo",
            is_active=True,
        )
        self.url = reverse("report-create", kwargs={"app_id": self.application.id})
        self.valid_b64 = base64.b64encode(b"fake-image-data").decode("utf-8")

    def test_throttle_limits_requests(self):
        payload = {
            "title": "Throttle test",
            "description": "Testing rate limiting here.",
            "attachments": [],
        }
        r1 = self.client.post(self.url, payload, format="json", REMOTE_ADDR="10.0.0.1")
        r2 = self.client.post(self.url, payload, format="json", REMOTE_ADDR="10.0.0.1")
        r3 = self.client.post(self.url, payload, format="json", REMOTE_ADDR="10.0.0.1")

        assert r1.status_code == status.HTTP_201_CREATED
        assert r2.status_code == status.HTTP_201_CREATED
        assert r3.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_throttle_per_ip(self):
        payload = {
            "title": "Throttle test",
            "description": "Testing rate limiting per IP.",
            "attachments": [],
        }
        r1 = self.client.post(self.url, payload, format="json", REMOTE_ADDR="10.0.0.1")
        r2 = self.client.post(self.url, payload, format="json", REMOTE_ADDR="10.0.0.1")
        r3 = self.client.post(self.url, payload, format="json", REMOTE_ADDR="10.0.0.2")

        assert r1.status_code == status.HTTP_201_CREATED
        assert r2.status_code == status.HTTP_201_CREATED
        assert r3.status_code == status.HTTP_201_CREATED
