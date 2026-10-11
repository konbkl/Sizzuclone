import random
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus

import config # 🟢 ZAROORI IMPORT
from SHIVMUSIC.core.call import ANJALI
from SHIVMUSIC.utils.database import is_music_playing, music_off # 🟢 is_music_playing ADD KIYA
from config import BANNED_USERS

# ✅ Kurigram Button Style Import
from button import ButtonStyle

# ✅ IMPORT NEW ADMIN CHECKER
from SHIVMUSIC.cplugin.utils.decorators.admins import AdminRightsCheck

# ==========================================
# 🔥 PREMIUM EMOJIS & SMART BUTTON HELPER
# ==========================================
PREMIUM_EMOJIS = [
    "5422831825178206894", 
    "5368324170673489600",
    "5206607081334906820",
    "5206380668048496464"
]

def action_btn(text, callback_data=None, url=None, style=ButtonStyle.PRIMARY, use_emoji=False):
    kwargs = {"text": text, "style": style}
    if callback_data: 
        kwargs["callback_data"] = callback_data
    if url: 
        kwargs["url"] = url
    if use_emoji: 
        kwargs["icon_custom_emoji_id"] = random.choice(PREMIUM_EMOJIS)
    return InlineKeyboardButton(**kwargs)

# ==========================================
# 🛑 PAUSE COMMAND EXECUTION
# ==========================================

@Client.on_message(filters.command(["pause", "cpause"]) & filters.group & ~BANNED_USERS)
@AdminRightsCheck 
async def pause_admin(cli: Client, message: Message, _, chat_id):
    # AdminRightsCheck already handles normal admins, sudoers, and clone owners.
    # A second Telegram-admin check here used to reject valid clone owners.
    if not await is_music_playing(chat_id):
        return await message.reply_text(_["admin_1"])

    await ANJALI.pause_stream(chat_id)
    await music_off(chat_id)

    # Inline Buttons setup with Kurigram Styles
    buttons = [
        [
            action_btn("ʀᴇsᴜᴍᴇ ▷", callback_data=f"ADMIN Resume|{chat_id}", style=ButtonStyle.SUCCESS),
            action_btn("ʀᴇᴘʟᴀʏ ↺", callback_data=f"ADMIN Replay|{chat_id}", style=ButtonStyle.PRIMARY),
        ],
        [ 
            action_btn("✯ CLONE NOW ✯", url="https://t.me/SizzuMusicBot", style=ButtonStyle.PRIMARY, use_emoji=True)
        ],
    ]

    # Reply message
    await message.reply_text(
        _["admin_2"].format(message.from_user.mention),
        reply_markup=InlineKeyboardMarkup(buttons),
    )
