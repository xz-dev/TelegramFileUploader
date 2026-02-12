#!/usr/bin/env python3

from argparse import ArgumentParser
from dataclasses import dataclass
from os import environ

from telethon import TelegramClient
from telethon.tl.types import PeerChannel, PeerChat, PeerUser


@dataclass
class UploadResult:
    """Result of a file upload operation."""

    message_urls: list[str]
    message_ids: list[int]


def validate_env():
    """Validate required environment variables. Returns (api_id, api_hash, bot_token)."""
    api_id = environ.get("API_ID")
    if not api_id:
        print("API_ID is missing")
        exit(1)
    api_id = int(api_id)
    api_hash = environ.get("API_HASH")
    if not api_hash:
        print("API_HASH is missing")
        exit(1)
    bot_token = environ.get("BOT_TOKEN")
    if not bot_token:
        print("BOT_TOKEN is missing")
        exit(1)
    return api_id, api_hash, bot_token


def build_message_url(
    peer_id, message_id: int, chat_username: str | None = None
) -> str:
    """Build a Telegram message URL from peer info and message ID.

    Args:
        peer_id: The peer ID object from the message (PeerChannel, PeerChat, or PeerUser).
        message_id: The message ID.
        chat_username: The chat's public username, if available.

    Returns:
        A URL string like https://t.me/username/123 or https://t.me/c/channel_id/123.
    """
    if chat_username:
        return f"https://t.me/{chat_username}/{message_id}"

    if isinstance(peer_id, PeerChannel):
        return f"https://t.me/c/{peer_id.channel_id}/{message_id}"

    if isinstance(peer_id, PeerChat):
        return f"https://t.me/c/{peer_id.chat_id}/{message_id}"

    # PeerUser (direct message) - no web URL available
    return f"https://t.me/c/{peer_id.user_id}/{message_id}"


async def main(
    client: TelegramClient, to: str, message: str, files: list[str]
) -> UploadResult:
    """Upload files and send them as a grouped message to the target chat.

    Returns:
        UploadResult containing message URLs and IDs.
    """

    # Printing upload progress
    def callback(current, total):
        print(f"Uploaded: {current / total * 100}%")

    # Upload files
    uploaded_files = []
    for file in files:
        print(f"Uploading {file}")
        ufile = await client.upload_file(file, progress_callback=callback)
        print(f"Uploaded {file}")
        uploaded_files.append(ufile)

    print("Sending message")
    message_list = [None for i in range(len(uploaded_files) - 1)]
    message_list.append(message)
    sent_messages = await client.send_file(
        entity=to, file=uploaded_files, caption=message_list, progress_callback=callback
    )
    print("Sent message")

    # Normalize to list (single file returns a single Message, not a list)
    if not isinstance(sent_messages, list):
        sent_messages = [sent_messages]

    # Resolve chat username for public URL construction
    chat_username = None
    try:
        entity = await client.get_entity(to)
        chat_username = getattr(entity, "username", None)
    except Exception:
        pass

    # Build URLs for each message
    message_urls = []
    message_ids = []
    for msg in sent_messages:
        message_ids.append(msg.id)
        url = build_message_url(msg.peer_id, msg.id, chat_username)
        message_urls.append(url)

    return UploadResult(message_urls=message_urls, message_ids=message_ids)


def write_github_output(result: UploadResult):
    """Write upload results to GitHub Actions output file if running in CI."""
    github_output = environ.get("GITHUB_OUTPUT")
    if not github_output:
        return
    with open(github_output, "a") as f:
        f.write(f"message_urls={','.join(result.message_urls)}\n")
        f.write(f"message_ids={','.join(str(i) for i in result.message_ids)}\n")
        # First URL/ID as convenience outputs
        f.write(f"message_url={result.message_urls[0]}\n")
        f.write(f"message_id={result.message_ids[0]}\n")


def get_arg_parser():
    """Create the argument parser for CLI usage."""
    parser = ArgumentParser(prog="TelegramFileUploader", epilog="@GitHub:xz-dev")
    parser.add_argument("--to", help="Chat ID or username")
    parser.add_argument("--message", help="Message")
    parser.add_argument("--files", help="Files", nargs="+")
    return parser


def process_files_arg(files):
    """Process --files argument to handle newlines from GitHub Actions multi-line input."""
    processed_files = []
    for file_arg in files:
        processed_files.extend(
            [arg.strip() for arg in file_arg.splitlines() if arg.strip()]
        )
    return processed_files


async def async_main():
    api_id, api_hash, bot_token = validate_env()

    parser = get_arg_parser()
    args = parser.parse_args()

    if args.files:
        args.files = process_files_arg(args.files)

    bot = TelegramClient("bot", api_id, api_hash)
    await bot.start(bot_token=bot_token)
    try:
        result = await main(bot, args.to, args.message, args.files)
    finally:
        await bot.disconnect()

    # Output results
    for url in result.message_urls:
        print(f"Message URL: {url}")

    write_github_output(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(async_main())

    # Example:
    # python3 main.py --to "me" --message "Hello, World!" --files "file1.txt" "file2.txt"
