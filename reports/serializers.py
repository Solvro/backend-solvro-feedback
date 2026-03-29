import base64
import binascii
from typing import Any

from rest_framework import serializers

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}


class AttachmentInputSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    content_base64 = serializers.CharField()
    content_type = serializers.ChoiceField(choices=sorted(ALLOWED_CONTENT_TYPES))

    def validate_content_base64(self, value: str) -> str:
        """
        Validate that content_base64 is decodable base64 and within size limits.
        """
        # Limit base64 payload to ~7MB, which corresponds to roughly ~5MB raw file size.
        # This prevents Out Of Memory (OOM) errors from decoding huge payloads.
        if len(value) > 7_000_000:
            raise serializers.ValidationError("File size exceeds the 5MB limit.")

        try:
            base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError):
            raise serializers.ValidationError("Invalid base64 payload.")
        return value

    def validate_filename(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Filename cannot be empty.")
        return value


class ReporterSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    email = serializers.EmailField(required=False)


class ReportCreateSerializer(serializers.Serializer):
    title = serializers.CharField(min_length=3, max_length=200)
    description = serializers.CharField(min_length=10, max_length=10_000)
    diagnostics = serializers.JSONField(required=False)
    reporter = ReporterSerializer(required=False)
    metadata = serializers.JSONField(required=False)
    attachments = AttachmentInputSerializer(many=True, required=False)

    def validate_attachments(self, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(value) > 5:
            raise serializers.ValidationError("You can upload up to 5 attachments.")
        return value
