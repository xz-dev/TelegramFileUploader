"""Unit tests for pure functions in main.py (no network, no Telegram API)."""

import pytest
from unittest.mock import patch

from main import process_files_arg, get_arg_parser, validate_env


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
