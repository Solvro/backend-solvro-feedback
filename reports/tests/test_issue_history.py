import pytest

from reports.models import Application, Issue, IssueStatus


@pytest.mark.django_db
class TestIssueHistory:
    def test_history_created_on_issue_create(self):
        app = Application.objects.create(
            name="History App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="History Issue",
            description="Testing history tracking here.",
        )
        assert issue.history.count() == 1

    def test_history_on_issue_update(self):
        app = Application.objects.create(
            name="History Update App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Original Title",
            description="Testing history updates here.",
        )
        issue.title = "Updated Title"
        issue.save()
        assert issue.history.count() == 2

    def test_history_on_issue_delete(self):
        from reports.models import HistoricalIssue

        app = Application.objects.create(
            name="History Delete App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Delete Me",
            description="Testing history on delete here.",
        )
        issue_id = issue.id
        issue.delete()
        assert HistoricalIssue.objects.filter(id=issue_id).count() >= 1

    def test_history_contains_status_change(self):
        app = Application.objects.create(
            name="History Status App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Status Change",
            description="Testing status change in history.",
        )
        issue.status = IssueStatus.VERIFIED
        issue.save()
        assert issue.history.count() == 2

    def test_history_records_old_values(self):
        app = Application.objects.create(
            name="History Old Values App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Original",
            description="Testing old values in history.",
        )
        issue.title = "Modified"
        issue.save()
        history = issue.history.all()
        assert history.count() == 2
        first_record = history.order_by("history_date").first()
        assert first_record.title == "Original"

    def test_history_model_exists(self):
        from reports.models import HistoricalIssue

        assert HistoricalIssue is not None

    def test_history_type_on_create(self):
        app = Application.objects.create(
            name="History Type App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Type Test",
            description="Testing history type on create.",
        )
        history = issue.history.first()
        assert history.history_type == "+"

    def test_history_type_on_update(self):
        app = Application.objects.create(
            name="History Update Type App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Update Type",
            description="Testing history type on update.",
        )
        issue.title = "Updated"
        issue.save()
        history = issue.history.order_by("history_date").last()
        assert history.history_type == "~"

    def test_history_type_on_delete(self):
        from reports.models import HistoricalIssue

        app = Application.objects.create(
            name="History Delete Type App",
            repo_url="https://github.com/test/repo",
        )
        issue = Issue.objects.create(
            application=app,
            title="Delete Type",
            description="Testing history type on delete.",
        )
        issue_id = issue.id
        issue.delete()
        history = HistoricalIssue.objects.filter(id=issue_id).first()
        assert history.history_type == "-"
