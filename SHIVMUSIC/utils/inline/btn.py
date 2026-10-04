"""Premium-aware inline buttons.

Telegram only shows ``icon_custom_emoji_id`` on bot buttons when the bot's
OWNER has Telegram Premium. This module decides, per bot, whether premium
icons can be used:

    PREMIUM_BUTTONS=auto  (default)  -> check the bot owner's Premium status
    PREMIUM_BUTTONS=on               -> always use premium icons
    PREMIUM_BUTTONS=off              -> always use normal emoji buttons

* Premium owner  -> icon + short label   (compact, premium look)
* Normal owner   -> plain emoji + label  (no custom-emoji, never errors)

A one-time patch of ``InlineKeyboardButton`` drops ``icon_custom_emoji_id``
everywhere in the project when premium icons are not allowed, so all the old
buttons stay safe too.
"""

import asyncio
import contextvars
import os
import time
from typing import Optional

from pyrogram.types import InlineKeyboardButton

import config

PREMIUM_MODE = os.getenv("PREMIUM_BUTTONS", "auto").strip().lower()
_TTL = 30 * 60

# owner_id -> (is_premium, checked_at)
_cache: dict = {}
# lets one panel builder force premium on/off for a single bot (clones)
_force: contextvars.ContextVar = contextvars.ContextVar("btn_force_premium", default=None)


def icons_enabled() -> bool:
    """Sync check used while building buttons (reads cached owner status)."""
    forced = _force.get()
    if forced is not None:
        return bool(forced)
    if PREMIUM_MODE in ("on", "true", "1", "yes"):
        return True
    if PREMIUM_MODE in ("off", "false", "0", "no"):
        return False
    hit = _cache.get(config.OWNER_ID)
    return bool(hit and hit[0])


class premium_scope:
    """``with premium_scope(True/False/None): build buttons`` for one bot."""

    def __init__(self, value: Optional[bool]):
        self.value = value

    def __enter__(self):
        self._token = _force.set(self.value)

    def __exit__(self, *exc):
        _force.reset(self._token)


async def _owner_is_premium(client, owner_id: int) -> bool:
    now = time.time()
    hit = _cache.get(owner_id)
    if hit and now - hit[1] < _TTL:
        return hit[0]
    try:
        user = await client.get_users(owner_id)
        value = bool(getattr(user, "is_premium", False))
    except Exception:
        # Could not check (owner never started the bot, flood, ...): keep the
        # last known value, otherwise stay safe with normal buttons.
        value = hit[0] if hit else False
    _cache[owner_id] = (value, now)
    return value


async def client_premium(client) -> bool:
    """Is the owner of *this* bot client a Premium user? (main bot or clone)"""
    if PREMIUM_MODE in ("on", "true", "1", "yes"):
        return True
    if PREMIUM_MODE in ("off", "false", "0", "no"):
        return False

    from SHIVMUSIC import app

    try:
        bot_id = client.me.id if getattr(client, "me", None) else None
        main_id = app.me.id if getattr(app, "me", None) else None
    except Exception:
        bot_id = main_id = None

    owner_id = config.OWNER_ID
    if bot_id and main_id and bot_id != main_id:
        try:
            from SHIVMUSIC.utils.database.clonedb import get_owner_id_from_db

            owner_id = await get_owner_id_from_db(bot_id) or config.OWNER_ID
        except Exception:
            owner_id = config.OWNER_ID

    # Main bot owner is the global default, always resolved through the main app.
    return await _owner_is_premium(app if owner_id == config.OWNER_ID else client, owner_id)


async def _refresher():
    from SHIVMUSIC import app

    while True:
        try:
            await _owner_is_premium(app, config.OWNER_ID)
        except Exception:
            pass
        await asyncio.sleep(_TTL)


def start_premium_refresher():
    """Call once after the main bot started (fills the cache, keeps it fresh)."""
    try:
        asyncio.get_running_loop().create_task(_refresher())
    except RuntimeError:
        pass


# ---------------------------------------------------------------------------
# One-time patch: strip premium icons whenever they are not allowed.
# ---------------------------------------------------------------------------
if not getattr(InlineKeyboardButton, "_premium_guard", False):
    _orig_init = InlineKeyboardButton.__init__

    def _guarded_init(self, *args, **kwargs):
        if "icon_custom_emoji_id" in kwargs and (
            kwargs["icon_custom_emoji_id"] is None or not icons_enabled()
        ):
            kwargs.pop("icon_custom_emoji_id")
        _orig_init(self, *args, **kwargs)

    InlineKeyboardButton.__init__ = _guarded_init
    InlineKeyboardButton._premium_guard = True


# ---------------------------------------------------------------------------
# Helpers for building the compact play panel
# ---------------------------------------------------------------------------
def smart_btn(symbol: str, emoji: str, emoji_id=None, *, cb=None, url=None, style=None):
    """Icon-style control button.

    premium -> text=symbol (tiny) + premium icon
    normal  -> text=emoji (plain)
    """
    premium = icons_enabled() and emoji_id is not None
    kwargs = {"text": symbol if premium else emoji}
    if cb:
        kwargs["callback_data"] = cb
    if url:
        kwargs["url"] = url
    if style is not None:
        kwargs["style"] = style
    if premium:
        kwargs["icon_custom_emoji_id"] = int(emoji_id)
    return InlineKeyboardButton(**kwargs)


def smart_label(emoji: str, text: str) -> str:
    """Label for text buttons: premium shows icon via id, normal shows emoji."""
    return text if icons_enabled() else f"{emoji} {text}"
