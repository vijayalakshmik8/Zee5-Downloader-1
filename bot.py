import logging
import os

import pyrogram
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


if __name__ == "__main__":
    missing = []
    if not Config.TG_BOT_TOKEN:
        missing.append("TG_BOT_TOKEN")
    if not Config.APP_ID:
        missing.append("APP_ID")
    if not Config.API_HASH:
        missing.append("API_HASH")

    if missing:
        raise SystemExit(
            "Missing environment variables: " + ", ".join(missing)
            + ". See .env.example / README.md."
        )

    os.makedirs(Config.DOWNLOAD_LOCATION, exist_ok=True)

    app = pyrogram.Client(
        "Zee5",
        bot_token=Config.TG_BOT_TOKEN,
        api_id=Config.APP_ID,
        api_hash=Config.API_HASH,
        plugins={"root": "plugins"},
    )
    app.run()
