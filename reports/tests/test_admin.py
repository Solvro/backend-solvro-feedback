from django.test import SimpleTestCase

from reports.admin import ApplicationAdmin, IssueAdmin, IssueAttachmentAdmin
from reports.models import IssueStatus


class TestApplicationAdmin(SimpleTestCase):
    def test_list_display(self):
        assert ApplicationAdmin.list_display == ("name", "is_active", "repo_url")

    def test_list_filter(self):
        assert ApplicationAdmin.list_filter == ("is_active",)

    def test_search_fields(self):
        assert ApplicationAdmin.search_fields == ("name", "repo_url")


class TestIssueAdmin(SimpleTestCase):
    def test_list_display(self):
        assert "title" in IssueAdmin.list_display
        assert "application" in IssueAdmin.list_display

    def test_list_filter(self):
        assert "status" in IssueAdmin.list_filter
        assert "application" in IssueAdmin.list_filter

    def test_search_fields(self):
        assert "title" in IssueAdmin.search_fields
        assert "description" in IssueAdmin.search_fields

    def test_readonly_fields(self):
        assert "created_at" in IssueAdmin.readonly_fields
        assert "updated_at" in IssueAdmin.readonly_fields


class TestIssueAttachmentAdmin(SimpleTestCase):
    def test_list_display(self):
        assert IssueAttachmentAdmin.list_display == (
            "filename",
            "issue",
            "content_type",
            "size",
            "created_at",
        )

    def test_search_fields(self):
        assert IssueAttachmentAdmin.search_fields == ("filename", "issue__title")

    def test_readonly_fields(self):
        assert IssueAttachmentAdmin.readonly_fields == ("created_at",)


class TestIssueStatus(SimpleTestCase):
    def test_status_new(self):
        assert IssueStatus.NEW == "NEW"

    def test_status_verified(self):
        assert IssueStatus.VERIFIED == "VERIFIED"

    def test_status_github_created(self):
        assert IssueStatus.GITHUB_CREATED == "GITHUB_CREATED"

    def test_status_rejected(self):
        assert IssueStatus.REJECTED == "REJECTED"

    def test_status_labels(self):
        assert IssueStatus.choices == [
            ("NEW", "New"),
            ("VERIFIED", "Verified"),
            ("GITHUB_CREATED", "GitHub created"),
            ("REJECTED", "Rejected"),
        ]
