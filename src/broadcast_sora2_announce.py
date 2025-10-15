import asyncio
import logging
from pathlib import Path
from typing import Iterable

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from sqlalchemy import select

from bot.container import Container
from bot.database.models import UserOrm


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("broadcast_sora2")


MESSAGE_TEXT = (
    "Бежит по воде и приходит первым — и всё это создано в Sora 2 🎬\n\n"
    "Создавай такие же видео из текстового промта \n"
    "👉 @vento\_toolbot\n"
    "Канал с готовыми промтами \n"
    "👉 [Vento Промты](https://t.me/ventoprompt)"
)

VIDEO_FILENAME = "IMG_6323.MP4"


def build_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📹 Создать видео", callback_data="sora2:open")]
        ]
    )


async def fetch_all_chat_ids(container: Container) -> list[int]:
    db = container.db()
    async with db.session_scope() as session:
        res = await session.scalars(
            select(UserOrm.telegram_id).where(UserOrm.is_blocked.is_(False))
        )
        ids = list(res.all())
    unique_ids = sorted({int(i) for i in ids if i is not None})
    logger.info("Loaded %d user chat_ids for broadcast", len(unique_ids))
    return unique_ids


async def _send_text(bot: Bot, chat_id: int, kb: InlineKeyboardMarkup) -> bool:
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=MESSAGE_TEXT,
            reply_markup=kb,
            disable_web_page_preview=True,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return True
    except TelegramRetryAfter as e:
        delay = getattr(e, "retry_after", 3)
        logger.warning("Flood control for %s, sleeping %.1fs", chat_id, delay)
        await asyncio.sleep(float(delay))
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=MESSAGE_TEXT,
                reply_markup=kb,
                disable_web_page_preview=True,
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            return True
        except Exception as e2:
            logger.error("Retry failed for %s: %s", chat_id, repr(e2))
            return False
    except (TelegramForbiddenError, TelegramBadRequest) as e:
        logger.info("Skip %s due to Telegram error: %s", chat_id, e.__class__.__name__)
        return False
    except TelegramAPIError as e:
        logger.info("Skip %s due to Telegram API error: %s", chat_id, e)
        return False
    except Exception as e:
        logger.exception("Unexpected error sending to %s: %s", chat_id, repr(e))
        return False


async def _send_video(bot: Bot, chat_id: int, kb: InlineKeyboardMarkup, video: str | FSInputFile) -> bool:
    try:
        await bot.send_video(
            chat_id=chat_id,
            video=video,
            caption=MESSAGE_TEXT,
            reply_markup=kb,
            supports_streaming=True,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return True
    except TelegramRetryAfter as e:
        delay = getattr(e, "retry_after", 3)
        logger.warning("Flood control (video) for %s, sleeping %.1fs", chat_id, delay)
        await asyncio.sleep(float(delay))
        try:
            await bot.send_video(
                chat_id=chat_id,
                video=video,
                caption=MESSAGE_TEXT,
                reply_markup=kb,
                supports_streaming=True,
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            return True
        except Exception as e2:
            logger.error("Video retry failed for %s: %s", chat_id, repr(e2))
            return False
    except (TelegramForbiddenError, TelegramBadRequest) as e:
        logger.info("Skip %s due to Telegram error (video): %s", chat_id, e.__class__.__name__)
        return False
    except TelegramAPIError as e:
        logger.info("Skip %s due to Telegram API error (video): %s", chat_id, e)
        return False
    except Exception as e:
        logger.exception("Unexpected error sending video to %s: %s", chat_id, repr(e))
        return False


async def broadcast(container: Container, chat_ids: Iterable[int]) -> None:
    bot: Bot = container.bot()
    kb = build_keyboard()

    sem = asyncio.Semaphore(4)  # lower concurrency for media uploads
    success = 0
    total = 0
    sent_with_media = 0

    # Video path inside container: /bot/code/IMG_6323.MP4
    video_path = (Path(__file__).resolve().parent / VIDEO_FILENAME)
    has_video_file = video_path.exists()
    file_id: str | None = None
    primed_chat: int | None = None

    # Prime upload to get reusable file_id
    if has_video_file:
        for cid in chat_ids:
            try:
                msg = await bot.send_video(
                    chat_id=cid,
                    video=FSInputFile(video_path.as_posix()),
                    caption=MESSAGE_TEXT,
                    reply_markup=kb,
                    supports_streaming=True,
                    parse_mode=ParseMode.MARKDOWN_V2,
                )
                primed_chat = cid
                if getattr(msg, "video", None) and getattr(msg.video, "file_id", None):
                    file_id = msg.video.file_id
                    sent_with_media += 1
                break
            except (TelegramForbiddenError, TelegramBadRequest):
                continue
            except TelegramRetryAfter as e:
                await asyncio.sleep(getattr(e, "retry_after", 3))
                continue
            except Exception:
                break
    else:
        logger.warning("Video file %s not found - sending text only.", video_path)

    async def worker(cid: int) -> None:
        nonlocal success, total, sent_with_media
        try:
            async with sem:
                if cid == primed_chat:
                    total += 1
                    success += 1
                    return

                if file_id:
                    ok = await _send_video(bot, cid, kb, file_id)
                    if ok:
                        sent_with_media += 1
                    else:
                        ok = await _send_text(bot, cid, kb)
                elif has_video_file:
                    ok = await _send_video(bot, cid, kb, FSInputFile(video_path.as_posix()))
                    if ok:
                        sent_with_media += 1
                    else:
                        ok = await _send_text(bot, cid, kb)
                else:
                    ok = await _send_text(bot, cid, kb)
                success += int(ok)
                total += 1
        except Exception as e:
            logger.info("Skip %s due to unexpected error in worker: %s", cid, repr(e))
            total += 1

    tasks = [asyncio.create_task(worker(cid)) for cid in chat_ids]
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info(
        "Broadcast finished: %d/%d delivered (media for at least %d)",
        success,
        total,
        sent_with_media,
    )


async def main() -> None:
    container = Container()
    chat_ids = await fetch_all_chat_ids(container)
    if not chat_ids:
        logger.warning("No recipients found — nothing to send.")
        return
    await broadcast(container, chat_ids)


if __name__ == "__main__":
    asyncio.run(main())
