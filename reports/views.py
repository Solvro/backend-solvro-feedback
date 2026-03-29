import base64
import uuid
from typing import Any

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import Application, Issue, IssueAttachment
from .serializers import ReportCreateSerializer


class PublicReportBurstRateThrottle(ScopedRateThrottle):
    scope = "public_report_burst"


class PublicReportSustainedRateThrottle(ScopedRateThrottle):
    scope = "public_report_sustained"


class PublicReportCreateView(APIView):
    """
    Public endpoint for creating reports:
    POST /report/<app_id>
    """

    authentication_classes: list[Any] = []
    permission_classes: list[Any] = []
    throttle_classes = [
        PublicReportBurstRateThrottle,
        PublicReportSustainedRateThrottle,
    ]

    def post(self, request, app_id: str, *args: Any, **kwargs: Any) -> Response:
        application = get_object_or_404(Application, id=app_id, is_active=True)

        serializer = ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        issue = Issue.objects.create(
            application=application,
            title=validated["title"],
            description=validated["description"],
            diagnostics=validated.get("diagnostics"),
        )

        attachments = validated.get("attachments", [])
        for attachment in attachments:
            raw_content = base64.b64decode(attachment["content_base64"])
            generated_key = (
                f"issues/{issue.id}/{uuid.uuid4().hex}_{attachment['filename']}"
            )

            # TODO (S3 integration): upload `raw_content` to S3-compatible storage.
            # For now we store a placeholder URL based on generated key.
            IssueAttachment.objects.create(
                issue=issue,
                original_filename=attachment["filename"],
                s3_key=generated_key,
                file_url=f"https://example-s3.local/{generated_key}",
                content_type=attachment["content_type"],
                size=len(raw_content),
            )

        return Response(
            {
                "issue_id": issue.id,
                "status": issue.status,
                "application_id": str(application.id),
                "created_at": issue.created_at,
            },
            status=status.HTTP_201_CREATED,
        )
