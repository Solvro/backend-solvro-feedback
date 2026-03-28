from django.contrib import admin

from .models import Application, Issue, IssueAttachment


class IssueAttachmentInline(admin.TabularInline):
    model = IssueAttachment
    extra = 0
    readonly_fields = (
        "original_filename",
        "s3_key",
        "file_url",
        "content_type",
        "size",
        "created_at",
    )
    can_delete = False


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "repo_url", "is_active")
    list_filter = ("is_active",)
    search_fields = ("id", "name", "repo_url")
    ordering = ("name",)


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "status",
        "application",
        "author",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "application", "created_at")
    search_fields = (
        "id",
        "title",
        "description",
        "application__name",
        "author__username",
        "author__email",
    )
    autocomplete_fields = ("application", "author")
    readonly_fields = (
        "created_at",
        "updated_at",
        "github_issue_number",
        "github_issue_url",
    )
    inlines = (IssueAttachmentInline,)
    ordering = ("-created_at",)


@admin.register(IssueAttachment)
class IssueAttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "issue",
        "original_filename",
        "content_type",
        "size",
        "created_at",
    )
    list_filter = ("content_type", "created_at")
    search_fields = ("id", "issue__title", "original_filename", "s3_key", "file_url")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
