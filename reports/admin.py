import logging

from django.contrib import admin

from .github_client import create_github_issue
from .models import Application, Issue, IssueAttachment, IssueStatus

logger = logging.getLogger(__name__)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "repo_url")
    list_filter = ("is_active",)
    search_fields = ("name", "repo_url")


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ("title", "application", "status", "created_at")
    list_filter = ("status", "application")
    search_fields = ("title", "description")
    readonly_fields = ("created_at", "updated_at")
    actions = [
        "mark_as_verified",
        "mark_as_rejected",
        "create_github_issue_action",
    ]

    @admin.action(description="Mark selected issues as Verified")
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(status=IssueStatus.VERIFIED)
        self.message_user(request, f"{updated} issue(s) marked as verified.")

    @admin.action(description="Mark selected issues as Rejected")
    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status=IssueStatus.REJECTED)
        self.message_user(request, f"{updated} issue(s) marked as rejected.")

    @admin.action(description="Create GitHub Issue for selected issues")
    def create_github_issue_action(self, request, queryset):
        created = 0
        errors = 0
        for issue in queryset:
            if issue.status not in (IssueStatus.VERIFIED, IssueStatus.NEW):
                self.message_user(
                    request,
                    f"Issue '{issue.title}' must be VERIFIED or NEW to create GitHub issue.",
                    level=admin.messages.ERROR,
                )
                errors += 1
                continue

            if issue.github_issue_number:
                self.message_user(
                    request,
                    f"Issue '{issue.title}' already has a GitHub issue #{issue.github_issue_number}.",
                    level=admin.messages.WARNING,
                )
                errors += 1
                continue

            try:
                result = create_github_issue(
                    repo_url=issue.application.repo_url,
                    title=issue.title,
                    body=issue.description,
                )
                issue.github_issue_number = result["number"]
                issue.github_issue_url = result["html_url"]
                issue.status = IssueStatus.GITHUB_CREATED
                issue.save(
                    update_fields=[
                        "github_issue_number",
                        "github_issue_url",
                        "status",
                    ]
                )
                created += 1
            except Exception as e:
                logger.exception("Failed to create GitHub issue for %s", issue.id)
                self.message_user(
                    request,
                    f"Failed to create GitHub issue for '{issue.title}': {e}",
                    level=admin.messages.ERROR,
                )
                errors += 1

        self.message_user(
            request,
            f"Created {created} GitHub issue(s). {errors} error(s).",
        )


@admin.register(IssueAttachment)
class IssueAttachmentAdmin(admin.ModelAdmin):
    list_display = ("filename", "issue", "content_type", "size", "created_at")
    search_fields = ("filename", "issue__title")
    readonly_fields = ("created_at",)
