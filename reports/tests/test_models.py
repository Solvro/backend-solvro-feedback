import uuid

from django.db import IntegrityError
from django.test import TestCase

from reports.models import Application, Issue, IssueAttachment, IssueStatus


class TestApplicationModel(TestCase):
    def test_create_application(self):
        app = Application.objects.create(
            name="Test App",
            repo_url="https://github.com/test/repo",
            is_active=True,
        )
        assert app.name == "Test App"
        assert app.is_active is True
        assert isinstance(app.id, uuid.UUID)

    def test_application_str(self):
        app = Application.objects.create(
            name="My App",
            repo_url="https://github.com/test/repo",
        )
        assert str(app) == "My App"

    def test_application_uuid_primary_key(self):
        app = Application.objects.create(
            name="UUID Test",
            repo_url="https://github.com/test/repo",
        )
        assert isinstance(app.id, uuid.UUID)

    def test_application_unique_name(self):
        Application.objects.create(
            name="Unique App",
            repo_url="https://github.com/test/repo",
        )
        with self.assertRaises(IntegrityError):
            Application.objects.create(
                name="Unique App",
                repo_url="https://github.com/test/repo2",
            )


class TestIssueModel(TestCase):
    def test_create_issue(self):
        app = Application.objects.create(
            name="Issue App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Bug report",
            description="This is a detailed bug description that is long enough.",
        )
        assert issue.title == "Bug report"
        assert issue.status == IssueStatus.NEW
        assert issue.application == app

    def test_issue_str(self):
        app = Application.objects.create(
            name="Str App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Test Issue",
            description="Description for testing purposes here.",
        )
        assert str(issue) == "[NEW] Test Issue"

    def test_issue_status_choices(self):
        app = Application.objects.create(
            name="Status App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Status Test",
            description="Testing status choices here.",
            status=IssueStatus.VERIFIED,
        )
        assert issue.status == IssueStatus.VERIFIED

    def test_issue_github_fields(self):
        app = Application.objects.create(
            name="Github App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Github Issue",
            description="Testing github fields here.",
            github_issue_number=42,
            github_issue_url="https://github.com/test/repo/issues/42",
        )
        assert issue.github_issue_number == 42
        assert issue.github_issue_url == "https://github.com/test/repo/issues/42"

    def test_issue_diagnostics(self):
        app = Application.objects.create(
            name="Diag App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Diag Issue",
            description="Testing diagnostics field here.",
            diagnostics={"platform": "android", "version": "1.0"},
        )
        assert issue.diagnostics == {"platform": "android", "version": "1.0"}

    def test_issue_cascade_delete(self):
        app = Application.objects.create(
            name="Cascade App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Cascade Issue",
            description="Testing cascade delete here.",
        )
        app.delete()
        assert not Issue.objects.filter(id=issue.id).exists()

    def test_issue_ordering(self):
        app = Application.objects.create(
            name="Ordering App",
            repo_url="https://github.com/test/repo",
        )
        issue1 = Issue.objects.create(
            application=app,
            title="Old Issue",
            description="First issue created here for ordering.",
        )
        issue2 = Issue.objects.create(
            application=app,
            title="New Issue",
            description="Second issue created here for ordering.",
        )
        issues = list(Issue.objects.all())
        assert issues[0] == issue2
        assert issues[1] == issue1


class TestIssueAttachmentModel(TestCase):
    def test_create_attachment(self):
        app = Application.objects.create(
            name="Attach App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Attach Issue",
            description="Description for attachment test here.",
        )
        attachment = IssueAttachment.objects.create(
            issue=issue,
            filename="screenshot.png",
            s3_key="issues/1/abc123_screenshot.png",
            file_url="https://s3.example.com/issues/1/abc123_screenshot.png",
            content_type="image/png",
            size=1024,
        )
        assert attachment.filename == "screenshot.png"
        assert attachment.size == 1024
        assert attachment.issue == issue

    def test_attachment_str(self):
        app = Application.objects.create(
            name="Str Attach App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Str Attach Issue",
            description="Description for str test here.",
        )
        attachment = IssueAttachment.objects.create(
            issue=issue,
            filename="test.png",
            s3_key="issues/1/test.png",
            file_url="https://s3.example.com/test.png",
            content_type="image/png",
            size=512,
        )
        assert str(attachment) == "test.png"

    def test_attachment_cascade_delete(self):
        app = Application.objects.create(
            name="Cascade Attach App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Cascade Attach Issue",
            description="Testing cascade delete for attachments.",
        )
        attachment = IssueAttachment.objects.create(
            issue=issue,
            filename="test.png",
            s3_key="issues/1/test.png",
            file_url="https://s3.example.com/test.png",
            content_type="image/png",
            size=512,
        )
        issue.delete()
        assert not IssueAttachment.objects.filter(id=attachment.id).exists()

    def test_attachment_ordering(self):
        app = Application.objects.create(
            name="Ordering Attach App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Ordering Attach Issue",
            description="Testing attachment ordering here.",
        )
        att1 = IssueAttachment.objects.create(
            issue=issue,
            filename="first.png",
            s3_key="issues/1/first.png",
            file_url="https://s3.example.com/first.png",
            content_type="image/png",
            size=100,
        )
        att2 = IssueAttachment.objects.create(
            issue=issue,
            filename="second.png",
            s3_key="issues/1/second.png",
            file_url="https://s3.example.com/second.png",
            content_type="image/png",
            size=200,
        )
        attachments = list(IssueAttachment.objects.filter(issue=issue))
        assert attachments[0] == att1
        assert attachments[1] == att2


class TestIssueStatusChoices(TestCase):
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
