from unittest.mock import MagicMock

import pytest
from django.contrib.admin import AdminSite
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

from reports.admin import IssueAdmin
from reports.models import Application, Issue, IssueStatus


def _make_admin_request():
    factory = RequestFactory()
    request = factory.get("/admin/reports/issue/")
    request.user = MagicMock()
    request.user.is_superuser = True
    SessionMiddleware(lambda req: None).process_request(request)
    MessageMiddleware(lambda req: None).process_request(request)
    return request


@pytest.mark.django_db
class TestAdminStatusActions:
    def test_mark_as_verified(self):
        site = AdminSite()
        admin_obj = IssueAdmin(Issue, site)
        app = Application.objects.create(
            name="Admin App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Verify Me",
            description="Testing verification here.",
            status=IssueStatus.NEW,
        )
        request = _make_admin_request()
        admin_obj.mark_as_verified(request, Issue.objects.filter(id=issue.id))
        issue.refresh_from_db()
        assert issue.status == IssueStatus.VERIFIED

    def test_mark_as_rejected(self):
        site = AdminSite()
        admin_obj = IssueAdmin(Issue, site)
        app = Application.objects.create(
            name="Reject App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Reject Me",
            description="Testing rejection here.",
            status=IssueStatus.NEW,
        )
        request = _make_admin_request()
        admin_obj.mark_as_rejected(request, Issue.objects.filter(id=issue.id))
        issue.refresh_from_db()
        assert issue.status == IssueStatus.REJECTED

    def test_mark_as_github_created(self):
        site = AdminSite()
        admin_obj = IssueAdmin(Issue, site)
        app = Application.objects.create(
            name="GH Create App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="GH Me",
            description="Testing github status here.",
            status=IssueStatus.NEW,
        )
        request = _make_admin_request()
        admin_obj.mark_as_github_created(request, Issue.objects.filter(id=issue.id))
        issue.refresh_from_db()
        assert issue.status == IssueStatus.GITHUB_CREATED

    def test_mark_as_verified_multiple(self):
        site = AdminSite()
        admin_obj = IssueAdmin(Issue, site)
        app = Application.objects.create(
            name="Multiple App",
            repo_url="https://github.com/test/repo",
        )
        issue1 = Issue.objects.create(
            application=app,
            title="Issue 1",
            description="First issue for multiple test.",
            status=IssueStatus.NEW,
        )
        issue2 = Issue.objects.create(
            application=app,
            title="Issue 2",
            description="Second issue for multiple test.",
            status=IssueStatus.NEW,
        )
        request = _make_admin_request()
        queryset = Issue.objects.filter(id__in=[issue1.id, issue2.id])
        admin_obj.mark_as_verified(request, queryset)
        issue1.refresh_from_db()
        issue2.refresh_from_db()
        assert issue1.status == IssueStatus.VERIFIED
        assert issue2.status == IssueStatus.VERIFIED


@pytest.mark.django_db
class TestAdminStatusBadge:
    def test_status_badge_colors(self):
        colors = {
            IssueStatus.NEW: "orange",
            IssueStatus.VERIFIED: "blue",
            IssueStatus.GITHUB_CREATED: "green",
            IssueStatus.REJECTED: "red",
        }
        assert colors[IssueStatus.NEW] == "orange"
        assert colors[IssueStatus.VERIFIED] == "blue"
        assert colors[IssueStatus.GITHUB_CREATED] == "green"
        assert colors[IssueStatus.REJECTED] == "red"

    def test_status_badge_renders_html(self):
        site = AdminSite()
        admin_obj = IssueAdmin(Issue, site)
        app = Application.objects.create(
            name="Badge App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Badge Issue",
            description="Testing badge rendering.",
            status=IssueStatus.VERIFIED,
        )
        badge = admin_obj.status_badge(issue)
        assert "blue" in badge
        assert "Verified" in badge

    def test_status_badge_new_status(self):
        site = AdminSite()
        admin_obj = IssueAdmin(Issue, site)
        app = Application.objects.create(
            name="Badge New App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Badge New Issue",
            description="Testing badge for new status.",
            status=IssueStatus.NEW,
        )
        badge = admin_obj.status_badge(issue)
        assert "orange" in badge
        assert "New" in badge

    def test_status_badge_github_created(self):
        site = AdminSite()
        admin_obj = IssueAdmin(Issue, site)
        app = Application.objects.create(
            name="Badge GH App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Badge GH Issue",
            description="Testing badge for github created.",
            status=IssueStatus.GITHUB_CREATED,
        )
        badge = admin_obj.status_badge(issue)
        assert "green" in badge
        assert "GitHub created" in badge

    def test_status_badge_rejected(self):
        site = AdminSite()
        admin_obj = IssueAdmin(Issue, site)
        app = Application.objects.create(
            name="Badge Rejected App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Badge Rejected Issue",
            description="Testing badge for rejected.",
            status=IssueStatus.REJECTED,
        )
        badge = admin_obj.status_badge(issue)
        assert "red" in badge
        assert "Rejected" in badge
