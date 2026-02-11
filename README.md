# Telegram File Uploader

A GitHub Action (and standalone CLI tool) for uploading files to Telegram using [Telethon](https://github.com/LonamiWebs/Telethon). Upload build artifacts, logs, or any files directly to a Telegram chat as a grouped message.

## Features

- Upload multiple files as a single grouped message (album)
- Upload progress reporting
- Works as a GitHub Action or standalone CLI tool
- Docker support

## Prerequisites

- Python 3.9+
- A Telegram Bot Token from [BotFather](https://t.me/botfather)
- Telegram API credentials (`API_ID` and `API_HASH`) from [my.telegram.org](https://my.telegram.org/)

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `API_ID` | Yes | Your Telegram API ID (integer) |
| `API_HASH` | Yes | Your Telegram API hash |
| `BOT_TOKEN` | Yes | Bot token from BotFather |

## GitHub Action Usage

### Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `to-who` | Yes | The recipient (chat ID or username) |
| `message` | Yes | The message/caption to send with the files |
| `files` | Yes | File paths to upload, one file per line |

### Example Workflow

Create `.github/workflows/telegram-upload.yml`:

```yaml
name: Upload Files to Telegram

on: [push]

jobs:
  upload-to-telegram:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Upload files to Telegram
      uses: xz-dev/TelegramFileUploader@v1
      with:
        to-who: 'username_or_chat_id'
        message: 'Here are your files!'
        files: |
          /path/to/file1
          /path/to/file2
      env:
        API_ID: ${{ secrets.API_ID }}
        API_HASH: ${{ secrets.API_HASH }}
        BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
```

Set `API_ID`, `API_HASH`, and `BOT_TOKEN` in your repository's **Settings > Secrets and variables > Actions**.

For a real-world usage example, see the [UpgradeAll Android CI workflow](https://github.com/DUpdateSystem/UpgradeAll/blob/master/.github/workflows/android.yml).

## Standalone CLI Usage

```bash
pip install -r requirements.txt

export API_ID="your_api_id"
export API_HASH="your_api_hash"
export BOT_TOKEN="your_bot_token"

python3 main.py --to "chat_id_or_username" --message "Hello!" --files "file1.txt" "file2.txt"
```

## Docker Usage

```bash
docker build -t telegram-uploader .

docker run \
  -e API_ID="your_api_id" \
  -e API_HASH="your_api_hash" \
  -e BOT_TOKEN="your_bot_token" \
  telegram-uploader \
  --to "chat_id_or_username" --message "Hello!" --files "file1.txt"
```

## Running Tests

Install test dependencies:

```bash
pip install -r requirements.txt pytest pytest-asyncio
```

Run unit tests (no network required):

```bash
pytest tests/test_unit.py -v
```

Run integration tests (requires environment variables and real Telegram API access):

```bash
export API_ID="your_api_id"
export API_HASH="your_api_hash"
export BOT_TOKEN="your_bot_token"
export CHAT_ID="target_chat_id"

pytest tests/test_integration.py -v
```

## License

[MIT](LICENSE)
