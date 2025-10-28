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
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from bot.container import Container
from bot.database.models import UserOrm


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("broadcast_sora2")

NEW_MESSAGE_TEXT = (
    "*✌️ Два видео\. ☝️ Один промпт\.*\n\n"
    "🎥 *Sora 2* против *Veo 3\.1* — битва нейросетей\.\n\n"
    "⤵️ Проверь сам и реши, кто выглядит убедительнее: /start"
)

REPLY_MARKUP = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="🎟️ Больше токенов", callback_data="goto:replenish_broadcast")]]
)

# Desired media order for album broadcast
MEDIA_FILENAMES = [
    "broadcast1.MOV",
    "broadcast2.MOV",
]


def _is_video(path: Path) -> bool:
    return path.suffix.lower() in {".mp4", ".mov"}


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


async def _send_text(bot: Bot, chat_id: int) -> bool:
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=NEW_MESSAGE_TEXT,
            disable_web_page_preview=True,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=REPLY_MARKUP,
        )
        return True
    except TelegramRetryAfter as e:
        delay = getattr(e, "retry_after", 3)
        logger.warning("Flood control (text) for %s, sleeping %.1fs", chat_id, delay)
        await asyncio.sleep(float(delay))
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=NEW_MESSAGE_TEXT,
                disable_web_page_preview=True,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=REPLY_MARKUP,
            )
            return True
        except Exception as e2:
            logger.error("Text retry failed for %s: %s", chat_id, repr(e2))
            return False
    except (TelegramForbiddenError, TelegramBadRequest) as e:
        logger.info("Skip %s due to Telegram error (text): %s", chat_id, e.__class__.__name__)
        return False
    except TelegramAPIError as e:
        logger.info("Skip %s due to Telegram API error (text): %s", chat_id, e)
        return False
    except Exception as e:
        logger.exception("Unexpected error sending text to %s: %s", chat_id, repr(e))
        return False


async def _send_album(bot: Bot, chat_id: int, media_group: list) -> bool:
    try:
        await bot.send_media_group(chat_id=chat_id, media=media_group)
        return True
    except TelegramRetryAfter as e:
        delay = getattr(e, "retry_after", 3)
        logger.warning("Flood control (album) for %s, sleeping %.1fs", chat_id, delay)
        await asyncio.sleep(float(delay))
        try:
            await bot.send_media_group(chat_id=chat_id, media=media_group)
            return True
        except Exception as e2:
            logger.error("Album retry failed for %s: %s", chat_id, repr(e2))
            return False
    except (TelegramForbiddenError, TelegramBadRequest) as e:
        logger.info("Skip %s due to Telegram error (album): %s", chat_id, e)
        return False
    except TelegramAPIError as e:
        logger.info("Skip %s due to Telegram API error (album): %s", chat_id, e)
        return False
    except Exception as e:
        logger.exception("Unexpected error sending album to %s: %s", chat_id, repr(e))
        return False


async def _send_single(
    bot: Bot,
    chat_id: int,
    is_video: bool,
    media: str | FSInputFile,
) -> bool:
    try:
        if is_video:
            await bot.send_video(
                chat_id=chat_id,
                video=media,
                caption=NEW_MESSAGE_TEXT,
                supports_streaming=True,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=REPLY_MARKUP,
            )
        else:
            await bot.send_photo(
                chat_id=chat_id,
                photo=media,
                caption=NEW_MESSAGE_TEXT,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=REPLY_MARKUP,
            )
        return True
    except TelegramRetryAfter as e:
        delay = getattr(e, "retry_after", 3)
        logger.warning("Flood control (single) for %s, sleeping %.1fs", chat_id, delay)
        await asyncio.sleep(float(delay))
        try:
            if is_video:
                await bot.send_video(
                    chat_id=chat_id,
                    video=media,
                    caption=NEW_MESSAGE_TEXT,
                    supports_streaming=True,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=REPLY_MARKUP,
                )
            else:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=media,
                    caption=NEW_MESSAGE_TEXT,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=REPLY_MARKUP,
                )
            return True
        except Exception as e2:
            logger.error("Single retry failed for %s: %s", chat_id, repr(e2))
            return False
    except (TelegramForbiddenError, TelegramBadRequest) as e:
        logger.info("Skip %s due to Telegram error (single): %s", chat_id, e)
        return False
    except TelegramAPIError as e:
        logger.info("Skip %s due to Telegram API error (single): %s", chat_id, e)
        return False
    except Exception as e:
        logger.exception("Unexpected error sending single to %s: %s", chat_id, repr(e))
        return False


async def broadcast(container: Container, chat_ids: Iterable[int]) -> None:
    bot: Bot = container.bot()

    sem = asyncio.Semaphore(4)  # lower concurrency for media uploads
    success = 0
    total = 0
    sent_with_media = 0

    # Resolve media paths
    base_dir = Path(__file__).resolve().parent
    media_paths = [base_dir / name for name in MEDIA_FILENAMES]
    existing = [p for p in media_paths if p.exists()]
    if len(existing) == 0:
        logger.warning("No media files found; will send text only.")

    # Prime: upload to obtain file_ids
    file_ids: list[str | None] = [None] * len(media_paths)
    primed_chat: int | None = None
    single_idx: int | None = None
    if len(existing) >= 2:
        # Build media list for priming using FSInputFile for available items, skipping missing but keeping order
        media_for_prime = []
        prime_index_map: list[int] = []  # map from media_for_prime index to MEDIA_FILENAMES index
        for idx, path in enumerate(media_paths):
            if path.exists():
                if _is_video(path):
                    media_for_prime.append(InputMediaVideo(media=FSInputFile(path.as_posix())))
                else:
                    media_for_prime.append(InputMediaPhoto(media=FSInputFile(path.as_posix())))
                prime_index_map.append(idx)

        # Add caption to the first media in group
        if media_for_prime:
            media_for_prime[0].caption = NEW_MESSAGE_TEXT
            media_for_prime[0].parse_mode = ParseMode.MARKDOWN_V2

        for cid in chat_ids:
            try:
                msgs = await bot.send_media_group(chat_id=cid, media=media_for_prime)
                primed_chat = cid
                # Collect file_ids according to original desired order
                for i, msg in enumerate(msgs):
                    target_idx = prime_index_map[i]
                    if getattr(msg, "video", None) and getattr(msg.video, "file_id", None):
                        file_ids[target_idx] = msg.video.file_id
                    elif getattr(msg, "photo", None):
                        sizes = msg.photo or []
                        if sizes:
                            file_ids[target_idx] = sizes[-1].file_id
                sent_with_media += 1
                break
            except (TelegramForbiddenError, TelegramBadRequest):
                continue
            except TelegramRetryAfter as e:
                await asyncio.sleep(getattr(e, "retry_after", 3))
                continue
            except Exception:
                break
    elif len(existing) == 1:
        # Identify the single existing index
        for idx, path in enumerate(media_paths):
            if path.exists():
                single_idx = idx
                break
        if single_idx is not None:
            single_path = media_paths[single_idx]
            for cid in chat_ids:
                try:
                    if _is_video(single_path):
                        msg = await bot.send_video(
                            chat_id=cid,
                            video=FSInputFile(single_path.as_posix()),
                            caption=NEW_MESSAGE_TEXT,
                            supports_streaming=True,
                            parse_mode=ParseMode.MARKDOWN_V2,
                            reply_markup=REPLY_MARKUP,
                        )
                        primed_chat = cid
                        file_ids[single_idx] = getattr(getattr(msg, "video", None), "file_id", None)
                        sent_with_media += 1
                        break
                    else:
                        msg = await bot.send_photo(
                            chat_id=cid,
                            photo=FSInputFile(single_path.as_posix()),
                            caption=NEW_MESSAGE_TEXT,
                            parse_mode=ParseMode.MARKDOWN_V2,
                            reply_markup=REPLY_MARKUP,
                        )
                        primed_chat = cid
                        sizes = getattr(msg, "photo", None) or []
                        file_ids[single_idx] = sizes[-1].file_id if sizes else None
                        sent_with_media += 1
                        break
                except (TelegramForbiddenError, TelegramBadRequest):
                    continue
                except TelegramRetryAfter as e:
                    await asyncio.sleep(getattr(e, "retry_after", 3))
                    continue
                except Exception:
                    break

    async def worker(cid: int) -> None:
        nonlocal success, total, sent_with_media
        try:
            async with sem:
                if cid == primed_chat:
                    total += 1
                    success += 1
                    return

                delivered = False
                # Album case (2 or more media)
                if len(existing) >= 2:
                    media_group = []
                    first_added = False
                    for idx, path in enumerate(media_paths):
                        target = None
                        if file_ids[idx]:
                            target = file_ids[idx]
                        elif path.exists():
                            target = FSInputFile(path.as_posix())
                        if target is None:
                            continue

                        if _is_video(path):
                            item = InputMediaVideo(media=target)
                        else:
                            item = InputMediaPhoto(media=target)
                        if not first_added:
                            item.caption = NEW_MESSAGE_TEXT
                            item.parse_mode = ParseMode.MARKDOWN_V2
                            first_added = True
                        media_group.append(item)

                    if len(media_group) >= 2:
                        delivered = await _send_album(bot, cid, media_group)
                        if delivered:
                            sent_with_media += 1
                elif len(existing) == 1 and single_idx is not None:
                    path = media_paths[single_idx]
                    if file_ids[single_idx]:
                        if _is_video(path):
                            delivered = await _send_single(bot, cid, True, file_ids[single_idx])
                        else:
                            delivered = await _send_single(bot, cid, False, file_ids[single_idx])
                    elif path.exists():
                        if _is_video(path):
                            delivered = await _send_single(bot, cid, True, FSInputFile(path.as_posix()))
                        else:
                            delivered = await _send_single(bot, cid, False, FSInputFile(path.as_posix()))
                else:
                    delivered = await _send_text(bot, cid)

                success += int(delivered)
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
        logger.warning("No recipients found - nothing to send.")
        return
    await broadcast(container, chat_ids)

if __name__ == "__main__":
    asyncio.run(main())
