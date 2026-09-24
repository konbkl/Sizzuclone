import math
import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

import config
from SHIVMUSIC import app
from config import SUPPORT_CHAT, OWNER_USERNAME
from SHIVMUSIC.utils.formatters import time_to_seconds
from SHIVMUSIC.utils.decorators.language import language

# User ke custom button styles
from button import ButtonStyle

# ==========================================
# 🔥 PREMIUM EMOJIS LIST 🔥
# ==========================================
PREMIUM_EMOJIS = [
    "5422831825178206894", 
    "5368324170673489600",
    "5206607081334906820",
    "5206380668048496464"
]

# 🎨 Dynamic Color Generator (Random Styles)
def get_style_map():
    styles = [ButtonStyle.PRIMARY, ButtonStyle.SUCCESS, ButtonStyle.DANGER]
    random.shuffle(styles)
    # Row me kitne buttons hain uske hisaab se color return karega
    return {1: styles[0], 2: styles[1], 3: styles[2], 4: styles[0], 5: styles[1]}

# 🔘 Smart Button Creator
def create_btn(text, callback_data=None, url=None, style=ButtonStyle.PRIMARY, no_emoji=False):
    kwargs = {"text": text, "style": style}
    if callback_data: 
        kwargs["callback_data"] = callback_data
    if url: 
        kwargs["url"] = url
    if not no_emoji: 
        kwargs["icon_custom_emoji_id"] = random.choice(PREMIUM_EMOJIS)
        
    return InlineKeyboardButton(**kwargs)

# ==========================================
# 🛑 MAIN CLONE COMMAND LOGIC
# ==========================================
BOT_LINK = "https://t.me/SizzuMusicBot"

# ✅ Helper to safely get Random Start Image
def get_random_start_img():
    if config.START_IMG_URL:
        if isinstance(config.START_IMG_URL, list):
            return random.choice(config.START_IMG_URL)
        return config.START_IMG_URL
    return "https://d.uguu.se/AnYfJXGx.jpg" # Fallback Image


@Client.on_message(filters.command("clone"))
@language
async def ping_clone(client: Client, message: Message, _):
    # Har baar command run hone par naya random color layega
    style_map = get_style_map()
    
    # ✅ Random Photo Logic with Custom Smart Button
    await message.reply_photo(
        photo=get_random_start_img(),
        caption=_["NO_CLONE_MSG"],
        reply_markup=InlineKeyboardMarkup(
            [
                # Naya create_btn function use kiya gaya hai with dynamic color & emoji
                [create_btn("ɢᴏ ᴀɴᴅ ᴄʟᴏɴᴇ", url=BOT_LINK, style=style_map[1])]
            ]
        )
    )
