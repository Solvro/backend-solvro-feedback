import base64
import binascii
import os
from typing import Any

from rest_framework import serializers

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}


class AttachmentInputSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    content_base64 = serializers.CharField()
    content_type = serializers.ChoiceField(choices=sorted(ALLOWED_CONTENT_TYPES))

    # We will store the decoded bytes here during validation to avoid double-decoding
    decoded_bytes = serializers.HiddenField(default=b"")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        value = attrs.get("content_base64", "")
        # Limit base64 payload to ~7MB, which corresponds to roughly ~5MB raw file size.
        # This prevents Out Of Memory (OOM) errors from decoding huge payloads.
        if len(value) > 7_000_000:
            raise serializers.ValidationError(
                {"content_base64": "File size exceeds the 5MB limit."}
            )

        try:
            attrs["decoded_bytes"] = base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError):
            raise serializers.ValidationError(
                {"content_base64": "Invalid base64 payload."}
            )

        return attrs

    def validate_filename(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Filename cannot be empty.")

        # Normalize to just the basename to prevent directory traversal
        basename = os.path.basename(value)

        # Ensure the resulting filename is safe
        safe_chars = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-. "
        )
        sanitized = "".join(c for c in basename if c in safe_chars)

        if not sanitized.strip():
            raise serializers.ValidationError("Filename contains no valid characters.")

        return sanitized


class ReportCreateSerializer(serializers.Serializer):
    title = serializers.CharField(min_length=3, max_length=200)
    description = serializers.CharField(min_length=10, max_length=10_000)
    diagnostics = serializers.JSONField(required=False)
    attachments = AttachmentInputSerializer(many=True, required=False)

    def validate_attachments(self, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(value) > 5:
            raise serializers.ValidationError("You can upload up to 5 attachments.")
        return value
