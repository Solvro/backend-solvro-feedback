from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings

from reports.github_client import create_github_issue, parse_repo_url


@pytest.mark.django_db
class TestParseRepoUrl:
    def test_valid_url(self):
        owner, repo = parse_repo_url("https://github.com/solvro/testownik")
        assert owner == "solvro"
        assert repo == "testownik"

    def test_url_with_trailing_slash(self):
        owner, repo = parse_repo_url("https://github.com/solvro/testownik/")
        assert owner == "solvro"
        assert repo == "testownik"

    def test_invalid_url_too_short(self):
        with pytest.raises(ValueError, match="Invalid GitHub repo URL"):
            parse_repo_url("https://github.com/solvro")

    def test_invalid_url_not_github(self):
        with pytest.raises(ValueError, match="Invalid GitHub repo URL"):
            parse_repo_url("https://example.com/repo")

    def test_url_with_extra_path(self):
        owner, repo = parse_repo_url("https://github.com/owner/repo/")
        assert owner == "owner"
        assert repo == "repo"


@pytest.mark.django_db
class TestCreateGithubIssue:
    @override_settings(GITHUB_TOKEN="test-token")
    @patch("reports.github_client.requests.post")
    def test_create_issue_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "number": 42,
            "html_url": "https://github.com/test/repo/issues/42",
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = create_github_issue(
            repo_url="https://github.com/test/repo",
            title="Test Issue",
            body="Test body",
        )

        assert result["number"] == 42
        assert result["html_url"] == "https://github.com/test/repo/issues/42"
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args.kwargs["json"]["title"] == "Test Issue"
        assert call_args.kwargs["json"]["body"] == "Test body"

    def test_create_issue_no_token(self):
        with override_settings(GITHUB_TOKEN=""):
            with pytest.raises(ValueError, match="GITHUB_TOKEN is not configured"):
                create_github_issue(
                    repo_url="https://github.com/test/repo",
                    title="Test",
                    body="Body",
                )

    @override_settings(GITHUB_TOKEN="test-token")
    @patch("reports.github_client.requests.post")
    def test_create_issue_api_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_post.return_value = mock_response

        with pytest.raises(Exception):
            create_github_issue(
                repo_url="https://github.com/test/repo",
                title="Test Issue",
                body="Test body",
            )

    @override_settings(GITHUB_TOKEN="test-token")
    @patch("reports.github_client.requests.post")
    def test_create_issue_request_headers(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "number": 1,
            "html_url": "https://github.com/test/repo/issues/1",
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        create_github_issue(
            repo_url="https://github.com/test/repo",
            title="Test",
            body="Body",
        )

        call_args = mock_post.call_args
        headers = call_args.kwargs["headers"]
        assert headers["Accept"] == "application/vnd.github+json"
        assert headers["Authorization"] == "Bearer test-token"
        assert headers["X-GitHub-Api-Version"] == "2022-11-28"
