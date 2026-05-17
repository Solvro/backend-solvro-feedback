from django.contrib import admin

from .models import Application, Issue, IssueAttachment


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


@admin.register(IssueAttachment)
class IssueAttachmentAdmin(admin.ModelAdmin):
    list_display = ("filename", "issue", "content_type", "size", "created_at")
    search_fields = ("filename", "issue__title")
    readonly_fields = ("created_at",)
