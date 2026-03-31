import base64
import uuid

from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from reports.models import Application, Issue, IssueAttachment

TEST_REST_FRAMEWORK_NO_THROTTLE_INTERFERENCE = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "public_report_burst": "2/min",
        "public_report_sustained": "2/min",
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


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK_NO_THROTTLE_INTERFERENCE)
class PublicReportCreateViewTests(APITestCase):
    def setUp(self):
        cache.clear()
        from rest_framework.settings import api_settings

        from reports.views import (
            PublicReportBurstRateThrottle,
            PublicReportSustainedRateThrottle,
        )

        PublicReportBurstRateThrottle.THROTTLE_RATES = (
            api_settings.DEFAULT_THROTTLE_RATES
        )
        PublicReportSustainedRateThrottle.THROTTLE_RATES = (
            api_settings.DEFAULT_THROTTLE_RATES
        )
        self.application = Application.objects.create(
            name="Testownik",
            repo_url="https://github.com/solvro/testownik",
            is_active=True,
        )
        self.url = reverse("report-create", kwargs={"app_id": self.application.id})
        self.valid_attachment_b64 = base64.b64encode(b"fake-image-bytes").decode(
            "utf-8"
        )

    def _payload(self, attachments=None):
        return {
            "title": "Crash on login",
            "description": "App crashes when user taps login after entering credentials.",
            "diagnostics": {"platform": "android", "app_version": "1.2.3"},
            "attachments": attachments if attachments is not None else [],
        }

    def test_create_report_happy_path(self):
        payload = self._payload(
            attachments=[
                {
                    "filename": "screen.png",
                    "content_type": "image/png",
                    "content_base64": self.valid_attachment_b64,
                }
            ]
        )

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "NEW")
        self.assertEqual(response.data["application_id"], str(self.application.id))

        self.assertEqual(Issue.objects.count(), 1)
        issue = Issue.objects.first()
        self.assertEqual(issue.application_id, self.application.id)
        self.assertEqual(issue.title, payload["title"])
        self.assertEqual(issue.description, payload["description"])
        self.assertEqual(issue.status, "NEW")

        self.assertEqual(IssueAttachment.objects.count(), 1)
        attachment = IssueAttachment.objects.first()
        self.assertEqual(attachment.issue_id, issue.id)
        self.assertEqual(attachment.original_filename, "screen.png")
        self.assertEqual(attachment.content_type, "image/png")
        self.assertGreater(attachment.size, 0)

    def test_create_report_returns_404_for_unknown_application(self):
        unknown_url = reverse("report-create", kwargs={"app_id": uuid.uuid4()})

        response = self.client.post(unknown_url, self._payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Issue.objects.count(), 0)

    def test_create_report_rejects_more_than_five_attachments(self):
        attachments = [
            {
                "filename": f"screen-{i}.png",
                "content_type": "image/png",
                "content_base64": self.valid_attachment_b64,
            }
            for i in range(6)
        ]
        payload = self._payload(attachments=attachments)

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("attachments", response.data)
        self.assertEqual(Issue.objects.count(), 0)
        self.assertEqual(IssueAttachment.objects.count(), 0)

    def test_create_report_rejects_invalid_base64_attachment(self):
        payload = self._payload(
            attachments=[
                {
                    "filename": "broken.png",
                    "content_type": "image/png",
                    "content_base64": "not-valid-base64###",
                }
            ]
        )

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("attachments", response.data)
        self.assertEqual(Issue.objects.count(), 0)
        self.assertEqual(IssueAttachment.objects.count(), 0)


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK_THROTTLE_STRICT)
class PublicReportCreateThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()
        from rest_framework.settings import api_settings

        from reports.views import (
            PublicReportBurstRateThrottle,
            PublicReportSustainedRateThrottle,
        )

        PublicReportBurstRateThrottle.THROTTLE_RATES = (
            api_settings.DEFAULT_THROTTLE_RATES
        )
        PublicReportSustainedRateThrottle.THROTTLE_RATES = (
            api_settings.DEFAULT_THROTTLE_RATES
        )
        self.application = Application.objects.create(
            name="Testownik-Throttle",
            repo_url="https://github.com/solvro/testownik",
            is_active=True,
        )
        self.url = reverse("report-create", kwargs={"app_id": self.application.id})
        self.valid_attachment_b64 = base64.b64encode(b"fake-image-bytes").decode(
            "utf-8"
        )

    def test_create_report_is_rate_limited_by_ip(self):
        payload = {
            "title": "Crash on login",
            "description": "App crashes when user taps login after entering credentials.",
            "attachments": [
                {
                    "filename": "screen.png",
                    "content_type": "image/png",
                    "content_base64": self.valid_attachment_b64,
                }
            ],
        }

        r1 = self.client.post(self.url, payload, format="json", REMOTE_ADDR="10.0.0.10")
        r2 = self.client.post(self.url, payload, format="json", REMOTE_ADDR="10.0.0.10")
        r3 = self.client.post(self.url, payload, format="json", REMOTE_ADDR="10.0.0.10")

        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r3.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
