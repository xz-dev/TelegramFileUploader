"""Integration tests using real Telegram API via Telethon.

These tests require environment variables:
  - API_ID: Telegram API ID
  - API_HASH: Telegram API hash
  - BOT_TOKEN: Bot token from BotFather
  - CHAT_ID: Chat ID to send test messages to

Tests are skipped automatically when credentials are not available.
"""

import os
import tempfile
import pytest
import pytest_asyncio

from telethon import TelegramClient

from main import main, validate_env

# Skip all tests in this module if credentials are missing
REQUIRED_VARS = ["API_ID", "API_HASH", "BOT_TOKEN", "CHAT_ID"]
_missing = [v for v in REQUIRED_VARS if not os.environ.get(v)]
pytestmark = pytest.mark.skipif(
    len(_missing) > 0,
    reason=f"Missing environment variables: {', '.join(_missing)}",
)


@pytest_asyncio.fixture
async def telegram_client():
    """Create a real Telegram bot client within the test's own event loop."""
    api_id, api_hash, bot_token = validate_env()
    client = TelegramClient("test_bot", api_id, api_hash)
    await client.start(bot_token=bot_token)
    yield client
    await client.disconnect()


@pytest.fixture
def chat_id():
    """Target chat for test messages. Must be an integer for Telethon bot usage."""
    return int(os.environ["CHAT_ID"])


@pytest.fixture
def temp_files():
    """Create temporary test files, cleaned up after the test."""
    created = []

    def _make(count=1, content="test content", suffix=".txt"):
        for i in range(count):
            f = tempfile.NamedTemporaryFile(
                mode="w", suffix=suffix, delete=False, prefix=f"tg_test_{i}_"
            )
            f.write(f"{content} #{i}")
            f.close()
            created.append(f.name)
        return created if count > 1 else created[0]

    yield _make

    for path in created:
        try:
            os.unlink(path)
        except OSError:
            pass


class TestTelegramConnection:
    """Test that the bot can connect and authenticate."""

    @pytest.mark.asyncio
    async def test_bot_is_connected(self, telegram_client):
        assert telegram_client.is_connected()

    @pytest.mark.asyncio
    async def test_bot_is_authorized(self, telegram_client):
        me = await telegram_client.get_me()
        assert me is not None
        assert me.bot is True


class TestSingleFileUpload:
    """Test uploading a single file."""

    @pytest.mark.asyncio
    async def test_upload_single_file(self, telegram_client, chat_id, temp_files):
        filepath = temp_files(count=1, content="single file test")
        await main(telegram_client, chat_id, "CI: single file upload test", [filepath])

    @pytest.mark.asyncio
    async def test_upload_empty_file_raises(self, telegram_client, chat_id):
        """Telegram API rejects empty files (0 bytes) with FilePartsInvalidError."""
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, prefix="tg_empty_")
        f.close()
        try:
            with pytest.raises(Exception):
                await main(telegram_client, chat_id, "CI: empty file test", [f.name])
        finally:
            os.unlink(f.name)


class TestMultiFileUpload:
    """Test uploading multiple files as a group."""

    @pytest.mark.asyncio
    async def test_upload_two_files(self, telegram_client, chat_id, temp_files):
        files = temp_files(count=2, content="multi file test")
        await main(telegram_client, chat_id, "CI: two files upload test", files)

    @pytest.mark.asyncio
    async def test_upload_three_files(self, telegram_client, chat_id, temp_files):
        files = temp_files(count=3, content="three files")
        await main(telegram_client, chat_id, "CI: three files upload test", files)


class TestFileTypes:
    """Test uploading files with different extensions."""

    @pytest.mark.asyncio
    async def test_upload_binary_file(self, telegram_client, chat_id):
        """Binary files should upload without issues."""
        f = tempfile.NamedTemporaryFile(mode="wb", suffix=".bin", delete=False, prefix="tg_bin_")
        f.write(b"\x00\x01\x02\x03" * 256)
        f.close()
        try:
            await main(telegram_client, chat_id, "CI: binary file test", [f.name])
        finally:
            os.unlink(f.name)


class TestMessageContent:
    """Test various message/caption scenarios."""

    @pytest.mark.asyncio
    async def test_message_with_special_chars(self, telegram_client, chat_id, temp_files):
        filepath = temp_files(count=1)
        await main(telegram_client, chat_id, "CI test: <b>bold</b> & special chars!@#$%", [filepath])

    @pytest.mark.asyncio
    async def test_empty_message(self, telegram_client, chat_id, temp_files):
        filepath = temp_files(count=1)
        await main(telegram_client, chat_id, "", [filepath])


class TestErrorHandling:
    """Test that errors from Telethon propagate correctly."""

    @pytest.mark.asyncio
    async def test_nonexistent_file_raises(self, telegram_client, chat_id):
        with pytest.raises(Exception):
            await main(telegram_client, chat_id, "should fail", ["/nonexistent/file.txt"])

    @pytest.mark.asyncio
    async def test_invalid_chat_id_raises(self, telegram_client, temp_files):
        filepath = temp_files(count=1)
        with pytest.raises(Exception):
            await main(telegram_client, "invalid_chat_id_99999999999", "test", [filepath])
