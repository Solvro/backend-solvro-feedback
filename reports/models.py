import uuid

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models


class IssueStatus(models.TextChoices):
    NEW = "NEW", "New"
    VERIFIED = "VERIFIED", "Verified"
    GITHUB_CREATED = "GITHUB_CREATED", "GitHub created"
    REJECTED = "REJECTED", "Rejected"


class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120, unique=True)
    repo_url = models.URLField(max_length=500)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Issue(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="issues",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_issues",
    )
    title = models.CharField(max_length=200, validators=[MinLengthValidator(3)])
    description = models.TextField(validators=[MinLengthValidator(10)])
    diagnostics = models.JSONField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=IssueStatus.choices,
        default=IssueStatus.NEW,
        db_index=True,
    )
    github_issue_number = models.PositiveIntegerField(null=True, blank=True)
    github_issue_url = models.URLField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.status}] {self.title}"


class IssueAttachment(models.Model):
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    original_filename = models.CharField(max_length=255)
    s3_key = models.CharField(max_length=500)
    file_url = models.URLField(max_length=1000)
    content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField(help_text="File size in bytes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return self.original_filename
