import base64
import uuid

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Application, Issue, IssueAttachment


class PublicReportCreateViewTests(APITestCase):
    def setUp(self):
        self.app = Application.objects.create(
            name="Test Application",
            repo_url="https://github.com/solvro/test-app",
            is_active=True,
        )
        self.inactive_app = Application.objects.create(
            name="Inactive Application",
            repo_url="https://github.com/solvro/inactive-app",
            is_active=False,
        )
        self.url = reverse("report-create", kwargs={"app_id": self.app.id})
        self.valid_payload = {
            "title": "App crashes on startup",
            "description": "When I open the app, it immediately crashes. See attached logs.",
            "diagnostics": {"os": "Android 13", "device": "Pixel 7"},
            "attachments": [
                {
                    "filename": "screenshot.png",
                    "content_base64": base64.b64encode(b"fake_image_bytes").decode(
                        "utf-8"
                    ),
                    "content_type": "image/png",
                }
            ],
        }

    def test_create_report_successfully(self):
        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("issue_id", response.data)

        self.assertEqual(Issue.objects.count(), 1)
        self.assertEqual(IssueAttachment.objects.count(), 1)

        issue = Issue.objects.first()
        self.assertEqual(issue.title, self.valid_payload["title"])
        self.assertEqual(issue.application, self.app)

        attachment = IssueAttachment.objects.first()
        self.assertEqual(attachment.original_filename, "screenshot.png")
        self.assertEqual(attachment.content_type, "image/png")

    def test_create_report_invalid_app_uuid(self):
        url = reverse("report-create", kwargs={"app_id": uuid.uuid4()})
        response = self.client.post(url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_report_inactive_app(self):
        url = reverse("report-create", kwargs={"app_id": self.inactive_app.id})
        response = self.client.post(url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_report_too_many_attachments(self):
        payload = self.valid_payload.copy()
        payload["attachments"] = [
            {
                "filename": f"file_{i}.png",
                "content_base64": base64.b64encode(b"test").decode("utf-8"),
                "content_type": "image/png",
            }
            for i in range(6)
        ]

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("attachments", response.data)

    def test_create_report_attachment_too_large(self):
        payload = self.valid_payload.copy()
        # Payload greater than 7_000_000 characters
        payload["attachments"] = [
            {
                "filename": "huge_file.png",
                "content_base64": "A" * 7_000_001,
                "content_type": "image/png",
            }
        ]

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("attachments", response.data)

    def test_create_report_invalid_base64(self):
        payload = self.valid_payload.copy()
        payload["attachments"][0]["content_base64"] = "invalid_base64_!@#"

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("attachments", response.data)

    def test_create_report_missing_required_fields(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)
        self.assertIn("description", response.data)
