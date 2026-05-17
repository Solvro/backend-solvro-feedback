import base64

from django.test import SimpleTestCase

from reports.serializers import (
    ALLOWED_CONTENT_TYPES,
    AttachmentInputSerializer,
    ReportCreateSerializer,
)


class TestAttachmentInputSerializer(SimpleTestCase):
    def test_valid_attachment(self):
        b64 = base64.b64encode(b"image-data").decode("utf-8")
        data = {
            "filename": "screenshot.png",
            "content_base64": b64,
            "content_type": "image/png",
        }
        serializer = AttachmentInputSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert "decoded_bytes" in serializer.validated_data

    def test_invalid_base64(self):
        data = {
            "filename": "bad.png",
            "content_base64": "!!!not-valid-base64!!!",
            "content_type": "image/png",
        }
        serializer = AttachmentInputSerializer(data=data)
        assert not serializer.is_valid()
        assert "content_base64" in serializer.errors

    def test_empty_filename(self):
        b64 = base64.b64encode(b"image-data").decode("utf-8")
        data = {
            "filename": "   ",
            "content_base64": b64,
            "content_type": "image/png",
        }
        serializer = AttachmentInputSerializer(data=data)
        assert not serializer.is_valid()
        assert "filename" in serializer.errors

    def test_filename_sanitization(self):
        b64 = base64.b64encode(b"image-data").decode("utf-8")
        data = {
            "filename": "../../../etc/passwd!@#.png",
            "content_base64": b64,
            "content_type": "image/png",
        }
        serializer = AttachmentInputSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["filename"] == "passwd.png"

    def test_filename_no_valid_chars(self):
        b64 = base64.b64encode(b"image-data").decode("utf-8")
        data = {
            "filename": "!@#$%^&*()",
            "content_base64": b64,
            "content_type": "image/png",
        }
        serializer = AttachmentInputSerializer(data=data)
        assert not serializer.is_valid()
        assert "filename" in serializer.errors

    def test_disallowed_content_type(self):
        b64 = base64.b64encode(b"exe-data").decode("utf-8")
        data = {
            "filename": "malware.exe",
            "content_base64": b64,
            "content_type": "application/x-msdownload",
        }
        serializer = AttachmentInputSerializer(data=data)
        assert not serializer.is_valid()
        assert "content_type" in serializer.errors

    def test_allowed_content_types(self):
        assert "image/png" in ALLOWED_CONTENT_TYPES
        assert "image/jpeg" in ALLOWED_CONTENT_TYPES
        assert "image/webp" in ALLOWED_CONTENT_TYPES

    def test_base64_too_large(self):
        large_b64 = base64.b64encode(b"x" * 7_000_001).decode("utf-8")
        data = {
            "filename": "large.png",
            "content_base64": large_b64,
            "content_type": "image/png",
        }
        serializer = AttachmentInputSerializer(data=data)
        assert not serializer.is_valid()
        assert "content_base64" in serializer.errors


class TestReportCreateSerializer(SimpleTestCase):
    def test_valid_report(self):
        data = {
            "title": "App crash",
            "description": "The application crashes on startup every time.",
            "diagnostics": {"os": "Android"},
            "attachments": [],
        }
        serializer = ReportCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_title_too_short(self):
        data = {
            "title": "Ab",
            "description": "The application crashes on startup every time.",
        }
        serializer = ReportCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "title" in serializer.errors

    def test_description_too_short(self):
        data = {
            "title": "App crash",
            "description": "Short",
        }
        serializer = ReportCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "description" in serializer.errors

    def test_too_many_attachments(self):
        b64 = base64.b64encode(b"data").decode("utf-8")
        attachments = [
            {
                "filename": f"file{i}.png",
                "content_base64": b64,
                "content_type": "image/png",
            }
            for i in range(6)
        ]
        data = {
            "title": "App crash",
            "description": "The application crashes on startup every time.",
            "attachments": attachments,
        }
        serializer = ReportCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "attachments" in serializer.errors

    def test_diagnostics_optional(self):
        data = {
            "title": "App crash",
            "description": "The application crashes on startup every time.",
        }
        serializer = ReportCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert "diagnostics" not in serializer.validated_data

    def test_attachments_optional(self):
        data = {
            "title": "App crash",
            "description": "The application crashes on startup every time.",
        }
        serializer = ReportCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert "attachments" not in serializer.validated_data
