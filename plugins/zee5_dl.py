import asyncio
import html
import logging
import os
import re
import shutil
import time
from urllib.parse import urlparse

import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import Config

logger = logging.getLogger(__name__)
USER_JOBS = {}

ALLOWED_MEDIA_EXTENSIONS = {
    ".mp4", ".m4v", ".mov", ".webm", ".m3u8", ".mpd",
    ".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav",
}


def _ydl_base_options():
    options = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "outtmpl": os.path.join(Config.DOWNLOAD_LOCATION, "%(title).150B_%(id)s.%(ext)s"),
    }
    cookie_path = getattr(Config, "COOKIES_FILE", "")
    if cookie_path and os.path.isfile(cookie_path):
        options["cookiefile"] = cookie_path
    return options


def _is_direct_media_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and os.path.splitext(parsed.path.lower())[1] in ALLOWED_MEDIA_EXTENSIONS


@Client.on_message(filters.private & filters.text & filters.regex(r"^https?://"))
async def capture_media(client, message):
    url = message.text.strip()

    # This repository's old Zee5 extractor rewrote DRM-labelled URLs.
    # Do not recreate or extend that DRM circumvention behavior.
    host = (urlparse(url).hostname or "").lower()
    if host == "zee5.com" or host.endswith(".zee5.com"):
        await message.reply_text(
            "This safe build does not extract Zee5 page links or bypass DRM. "
            "Use an official download option, or send a direct non-DRM media URL "
            "that you are authorized to download."
        )
        return

    if not _is_direct_media_url(url):
        await message.reply_text(
            "Please send a direct media URL ending in a supported media extension "
            "(for example .mp4, .mp3, .m3u8 or .webm). DRM-protected streams are not supported."
        )
        return

    status = await message.reply_text("🔎 Checking available media formats...")
    try:
        def inspect():
            with yt_dlp.YoutubeDL(_ydl_base_options()) as ydl:
                return ydl.extract_info(url, download=False)

        info = await asyncio.to_thread(inspect)
        if not info:
            raise RuntimeError("No media information was returned.")

        formats = info.get("formats") or []
        buttons = []
        seen = set()

        for item in reversed(formats):
            if item.get("vcodec") == "none":
                continue
            fmt_id = str(item.get("format_id", ""))
            if not fmt_id or len(fmt_id.encode("utf-8")) > 35 or fmt_id in seen:
                continue
            seen.add(fmt_id)

            height = item.get("height")
            note = item.get("format_note") or (f"{height}p" if height else item.get("format", "Video"))
            size = item.get("filesize") or item.get("filesize_approx")
            size_text = f" · {size / (1024 * 1024):.1f} MB" if size else ""
            label = f"🎬 {note}{size_text}"
            buttons.append(InlineKeyboardButton(label[:60], callback_data=f"video|{fmt_id}"))
            if len(buttons) >= 8:
                break

        keyboard_rows = [[button] for button in buttons]
        keyboard_rows.append([InlineKeyboardButton("🎵 MP3 Audio", callback_data="audio|mp3")])

        if not keyboard_rows:
            raise RuntimeError("No downloadable video formats were found.")

        USER_JOBS[message.from_user.id] = {
            "url": url,
            "title": info.get("title") or "Media",
        }
        await status.edit_text(
            f"Choose a format for: <b>{html.escape(info.get('title') or 'Media')}</b>",
            reply_markup=InlineKeyboardMarkup(keyboard_rows),
            parse_mode="html",
        )
    except Exception as exc:
        logger.exception("Media inspection failed")
        await status.edit_text(f"❌ Could not inspect this media: {html.escape(str(exc))}")


async def zee5_execute(client, query):
    user_id = query.from_user.id
    job = USER_JOBS.get(user_id)
    if not job:
        await query.answer("Link expired. Send the media URL again.", show_alert=True)
        return

    try:
        mode, selected = query.data.split("|", 1)
    except ValueError:
        await query.answer("Invalid selection.", show_alert=True)
        return

    await query.answer()
    status = await query.message.edit_text("⏬ Downloading media...")
    output_dir = os.path.join(Config.DOWNLOAD_LOCATION, str(user_id))
    os.makedirs(output_dir, exist_ok=True)
    filename = None

    try:
        options = _ydl_base_options()
        options["outtmpl"] = os.path.join(output_dir, "%(title).150B_%(id)s.%(ext)s")

        if mode == "audio":
            options.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })
        elif mode == "video":
            options.update({
                "format": f"{selected}+bestaudio/{selected}/best",
                "merge_output_format": "mp4",
            })
        else:
            raise RuntimeError("Unsupported media type.")

        def download():
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(job["url"], download=True)
                if not info:
                    raise RuntimeError("Download did not return media information.")
                prepared = ydl.prepare_filename(info)
                if mode == "audio":
                    prepared = os.path.splitext(prepared)[0] + ".mp3"
                elif not os.path.exists(prepared):
                    mp4_candidate = os.path.splitext(prepared)[0] + ".mp4"
                    if os.path.exists(mp4_candidate):
                        prepared = mp4_candidate
                return prepared, info

        filename, info = await asyncio.to_thread(download)
        if not filename or not os.path.isfile(filename):
            raise RuntimeError("Downloaded output file was not found.")

        size = os.path.getsize(filename)
        if size > Config.TG_MAX_FILE_SIZE:
            raise RuntimeError(
                f"File is {size / (1024 * 1024):.1f} MB, above the configured Telegram upload limit."
            )

        await status.edit_text("📤 Uploading to Telegram...")
        title = info.get("title") or job.get("title") or "Media"

        if mode == "audio":
            await client.send_audio(
                chat_id=query.message.chat.id,
                audio=filename,
                title=title[:64],
                caption=f"🎵 {html.escape(title)}",
                parse_mode="html",
            )
        else:
            await client.send_video(
                chat_id=query.message.chat.id,
                video=filename,
                caption=f"🎬 {html.escape(title)}",
                parse_mode="html",
                supports_streaming=True,
            )

        await status.delete()
    except Exception as exc:
        logger.exception("Media download/upload failed")
        await status.edit_text(f"❌ Failed: {html.escape(str(exc))}")
    finally:
        if filename and os.path.isfile(filename):
            try:
                os.remove(filename)
            except OSError:
                pass
        try:
            shutil.rmtree(output_dir, ignore_errors=True)
        except OSError:
            pass
