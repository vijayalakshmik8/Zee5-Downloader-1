import os


class Config:
    # Telegram credentials: set these as environment variables in Termux.
    TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
    APP_ID = int(os.environ.get("APP_ID", "0"))
    API_HASH = os.environ.get("API_HASH", "")

    AUTH_USERS = {
        int(x) for x in os.environ.get("AUTH_USERS", "").split()
        if x.isdigit()
    }
    BANNED_USERS = {
        int(x) for x in os.environ.get("BANNED_USERS", "").split()
        if x.isdigit()
    }

    DOWNLOAD_LOCATION = os.environ.get("DOWNLOAD_LOCATION", "./DOWNLOADS")
    UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "")
    TG_MAX_FILE_SIZE = int(os.environ.get("TG_MAX_FILE_SIZE", str(2_000_000_000)))
    CHUNK_SIZE = 1024 * 128
    DEF_THUMB_NAIL_VID_S = os.environ.get("DEF_THUMB_NAIL_VID_S", "")

    # Optional Netscape-format cookies for sites/media you are authorized to access.
    # This does not decrypt or bypass DRM-protected streams.
    COOKIES_FILE = os.environ.get("COOKIES_FILE", "")

    # SQLite works locally in Termux. Set DATABASE_URL for PostgreSQL if desired.
    DB_URI = os.environ.get("DATABASE_URL", "sqlite:///zee5_bot.db")
