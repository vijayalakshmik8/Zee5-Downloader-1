# Zee5 Downloader project — safe Termux setup

## Important limitation
This patched build does **not** extract Zee5 page links or bypass DRM. The previous
Zee5-specific code rewrote DRM-labelled URLs; that behavior has been removed.
This build only handles direct, non-DRM media URLs that yt-dlp can access and that
you are authorized to download. Cookies are optional authentication for supported
non-DRM sources; they do not decrypt DRM streams.

## Termux installation

```bash
pkg update && pkg upgrade -y
pkg install python ffmpeg git -y
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configure

Set your Telegram credentials in Termux before starting the bot:

```bash
export APP_ID="YOUR_API_ID"
export API_HASH="YOUR_API_HASH"
export TG_BOT_TOKEN="YOUR_BOT_TOKEN"
```

Optional settings:

```bash
export UPDATE_CHANNEL=""
export AUTH_USERS=""
export COOKIES_FILE="/path/to/cookies.txt"
```

`COOKIES_FILE` must point to a Netscape-format cookies file for a service/account
you are authorized to use. Do not publish or share your cookies file.

## Run

```bash
python bot.py
```

## Notes
- FFmpeg is required for MP3 conversion and audio/video merging.
- Local SQLite is used by default; PostgreSQL can be configured with `DATABASE_URL`.
- Do not use this bot to download DRM-protected or unauthorized content.
