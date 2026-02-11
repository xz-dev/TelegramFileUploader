"""Unit tests for pure functions in main.py (no network, no Telegram API)."""

import os
import tempfile
import pytest
from unittest.mock import patch

from telethon.tl.types import PeerChannel, PeerChat, PeerUser

from main import process_files_arg, get_arg_parser, validate_env, build_message_url, UploadResult, write_github_output


class TestProcessFilesArg:
    """Tests for the file argument processing logic."""

    def test_single_file(self):
        assert process_files_arg(["file1.txt"]) == ["file1.txt"]

    def test_multiple_separate_args(self):
        assert process_files_arg(["file1.txt", "file2.txt"]) == ["file1.txt", "file2.txt"]

    def test_multiline_input(self):
        """GitHub Actions passes multi-line input as a single string."""
        assert process_files_arg(["file1.txt\nfile2.txt"]) == ["file1.txt", "file2.txt"]

    def test_multiline_with_trailing_newline(self):
        assert process_files_arg(["file1.txt\nfile2.txt\n"]) == ["file1.txt", "file2.txt"]

    def test_multiline_with_carriage_return(self):
        """Windows-style line endings from GitHub Actions."""
        assert process_files_arg(["file1.txt\r\nfile2.txt\r\n"]) == ["file1.txt", "file2.txt"]

    def test_strips_leading_and_trailing_whitespace(self):
        assert process_files_arg(["  file1.txt  \n  file2.txt  "]) == ["file1.txt", "file2.txt"]

    def test_filters_empty_lines(self):
        assert process_files_arg(["file1.txt\n\n\nfile2.txt"]) == ["file1.txt", "file2.txt"]

    def test_filters_whitespace_only_lines(self):
        assert process_files_arg(["file1.txt\n   \n  \nfile2.txt"]) == ["file1.txt", "file2.txt"]

    def test_multiple_args_each_with_newlines(self):
        result = process_files_arg(["a.txt\nb.txt", "c.txt\nd.txt"])
        assert result == ["a.txt", "b.txt", "c.txt", "d.txt"]

    def test_empty_list(self):
        assert process_files_arg([]) == []

    def test_only_whitespace_input(self):
        assert process_files_arg(["  \n  \n  "]) == []

    def test_preserves_paths_with_spaces(self):
        """File paths may contain spaces - only strip leading/trailing."""
        assert process_files_arg(["path/to/my file.txt"]) == ["path/to/my file.txt"]

    def test_preserves_absolute_paths(self):
        assert process_files_arg(["/tmp/build/artifact.zip"]) == ["/tmp/build/artifact.zip"]


class TestGetArgParser:
    """Tests for CLI argument parsing."""

    def test_all_args_parsed(self):
        parser = get_arg_parser()
        args = parser.parse_args(["--to", "chat123", "--message", "hello", "--files", "a.txt", "b.txt"])
        assert args.to == "chat123"
        assert args.message == "hello"
        assert args.files == ["a.txt", "b.txt"]

    def test_single_file(self):
        parser = get_arg_parser()
        args = parser.parse_args(["--to", "x", "--message", "m", "--files", "only.txt"])
        assert args.files == ["only.txt"]

    def test_multiple_files(self):
        parser = get_arg_parser()
        args = parser.parse_args(["--to", "x", "--message", "m", "--files", "f1", "f2", "f3"])
        assert args.files == ["f1", "f2", "f3"]

    def test_no_args_defaults_to_none(self):
        parser = get_arg_parser()
        args = parser.parse_args([])
        assert args.to is None
        assert args.message is None
        assert args.files is None

    def test_message_with_spaces(self):
        parser = get_arg_parser()
        args = parser.parse_args(["--to", "x", "--message", "hello world", "--files", "f.txt"])
        assert args.message == "hello world"


class TestValidateEnv:
    """Tests for environment variable validation."""

    def test_all_env_vars_present(self):
        with patch.dict("os.environ", {"API_ID": "12345", "API_HASH": "abc123", "BOT_TOKEN": "tok:en"}, clear=True):
            api_id, api_hash, bot_token = validate_env()
            assert api_id == 12345
            assert api_hash == "abc123"
            assert bot_token == "tok:en"

    def test_missing_api_id_exits(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(SystemExit):
                validate_env()

    def test_missing_api_hash_exits(self):
        with patch.dict("os.environ", {"API_ID": "123"}, clear=True):
            with pytest.raises(SystemExit):
                validate_env()

    def test_missing_bot_token_exits(self):
        with patch.dict("os.environ", {"API_ID": "123", "API_HASH": "abc"}, clear=True):
            with pytest.raises(SystemExit):
                validate_env()

    def test_non_numeric_api_id_raises(self):
        with patch.dict("os.environ", {"API_ID": "not_a_number", "API_HASH": "abc", "BOT_TOKEN": "tok"}, clear=True):
            with pytest.raises(ValueError):
                validate_env()


class TestBuildMessageUrl:
    """Tests for building Telegram message URLs."""

    def test_public_channel_with_username(self):
        peer = PeerChannel(channel_id=123456)
        url = build_message_url(peer, 42, chat_username="mychannel")
        assert url == "https://t.me/mychannel/42"

    def test_private_channel_no_username(self):
        peer = PeerChannel(channel_id=123456)
        url = build_message_url(peer, 42)
        assert url == "https://t.me/c/123456/42"

    def test_private_channel_username_none(self):
        peer = PeerChannel(channel_id=789)
        url = build_message_url(peer, 10, chat_username=None)
        assert url == "https://t.me/c/789/10"

    def test_group_chat(self):
        peer = PeerChat(chat_id=654321)
        url = build_message_url(peer, 99)
        assert url == "https://t.me/c/654321/99"

    def test_group_chat_with_username(self):
        """Public groups with a username should use the username format."""
        peer = PeerChat(chat_id=654321)
        url = build_message_url(peer, 99, chat_username="mygroup")
        assert url == "https://t.me/mygroup/99"

    def test_direct_message(self):
        peer = PeerUser(user_id=111)
        url = build_message_url(peer, 5)
        assert url == "https://t.me/c/111/5"

    def test_direct_message_with_username(self):
        peer = PeerUser(user_id=111)
        url = build_message_url(peer, 5, chat_username="someuser")
        assert url == "https://t.me/someuser/5"

    def test_message_id_is_integer(self):
        peer = PeerChannel(channel_id=1)
        url = build_message_url(peer, 1)
        assert "/1" in url

    def test_large_ids(self):
        peer = PeerChannel(channel_id=1234567890123)
        url = build_message_url(peer, 999999)
        assert url == "https://t.me/c/1234567890123/999999"


class TestUploadResult:
    """Tests for the UploadResult dataclass."""

    def test_creation(self):
        result = UploadResult(
            message_urls=["https://t.me/c/123/1"],
            message_ids=[1],
        )
        assert result.message_urls == ["https://t.me/c/123/1"]
        assert result.message_ids == [1]

    def test_multiple_messages(self):
        result = UploadResult(
            message_urls=["https://t.me/c/123/1", "https://t.me/c/123/2"],
            message_ids=[1, 2],
        )
        assert len(result.message_urls) == 2
        assert len(result.message_ids) == 2


class TestWriteGithubOutput:
    """Tests for GitHub Actions output writing."""

    def test_no_github_output_env(self):
        """Should do nothing when GITHUB_OUTPUT is not set."""
        result = UploadResult(
            message_urls=["https://t.me/c/123/1"],
            message_ids=[1],
        )
        with patch.dict("os.environ", {}, clear=True):
            # Should not raise
            write_github_output(result)

    def test_writes_to_github_output_file(self):
        """Should write outputs to the GITHUB_OUTPUT file."""
        result = UploadResult(
            message_urls=["https://t.me/chan/1", "https://t.me/chan/2"],
            message_ids=[1, 2],
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            output_path = f.name

        try:
            with patch.dict("os.environ", {"GITHUB_OUTPUT": output_path}, clear=True):
                write_github_output(result)
            with open(output_path) as f:
                content = f.read()
            assert "message_urls=https://t.me/chan/1,https://t.me/chan/2" in content
            assert "message_ids=1,2" in content
            assert "message_url=https://t.me/chan/1" in content
            assert "message_id=1" in content
        finally:
            os.unlink(output_path)

    def test_single_message_output(self):
        """Single message should still produce all output keys."""
        result = UploadResult(
            message_urls=["https://t.me/test/5"],
            message_ids=[5],
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            output_path = f.name

        try:
            with patch.dict("os.environ", {"GITHUB_OUTPUT": output_path}, clear=True):
                write_github_output(result)
            with open(output_path) as f:
                content = f.read()
            assert "message_urls=https://t.me/test/5" in content
            assert "message_ids=5" in content
            assert "message_url=https://t.me/test/5" in content
            assert "message_id=5" in content
        finally:
            os.unlink(output_path)
