from django.contrib import admin
from django.utils.html import format_html

from .models import Application, Issue, IssueAttachment, IssueStatus


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "repo_url")
    list_filter = ("is_active",)
    search_fields = ("name", "repo_url")


class IssueAdmin(admin.ModelAdmin):
    list_display = ("title", "application", "status_badge", "created_at", "updated_at")
    list_filter = ("status", "application", "created_at")
    search_fields = ("title", "description")
    readonly_fields = ("created_at", "updated_at", "author", "application")
    fieldsets = (
        (None, {"fields": ("title", "description", "application", "author", "status")}),
        (
            "GitHub",
            {
                "fields": ("github_issue_number", "github_issue_url"),
                "classes": ("collapse",),
            },
        ),
        ("Diagnostics", {"fields": ("diagnostics",), "classes": ("collapse",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    actions = ["mark_as_verified", "mark_as_rejected", "mark_as_github_created"]

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        colors = {
            IssueStatus.NEW: "orange",
            IssueStatus.VERIFIED: "blue",
            IssueStatus.GITHUB_CREATED: "green",
            IssueStatus.REJECTED: "red",
        }
        color = colors.get(obj.status, "grey")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.action(description="Mark selected issues as Verified")
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(status=IssueStatus.VERIFIED)
        self.message_user(request, f"{updated} issue(s) marked as verified.")

    @admin.action(description="Mark selected issues as Rejected")
    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status=IssueStatus.REJECTED)
        self.message_user(request, f"{updated} issue(s) marked as rejected.")

    @admin.action(description="Mark selected issues as GitHub Created")
    def mark_as_github_created(self, request, queryset):
        updated = queryset.update(status=IssueStatus.GITHUB_CREATED)
        self.message_user(request, f"{updated} issue(s) marked as GitHub created.")


admin.site.register(Issue, IssueAdmin)


@admin.register(IssueAttachment)
class IssueAttachmentAdmin(admin.ModelAdmin):
    list_display = ("filename", "issue", "content_type", "size", "created_at")
    search_fields = ("filename", "issue__title")
    readonly_fields = ("created_at",)
