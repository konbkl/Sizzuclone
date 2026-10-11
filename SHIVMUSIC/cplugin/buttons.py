import math
import random
from config import SUPPORT_CHAT, OWNER_USERNAME
from SHIVMUSIC import app
import config
from SHIVMUSIC.utils.formatters import time_to_seconds

from button import ButtonStyle
from pyrogram.types import InlineKeyboardButton

# 🔥 PREMIUM EMOJIS LIST 🔥
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
    if callback_data: kwargs["callback_data"] = callback_data
    if url: kwargs["url"] = url
    if not no_emoji: kwargs["icon_custom_emoji_id"] = random.choice(PREMIUM_EMOJIS)
    return InlineKeyboardButton(**kwargs)

# --- HELPERS ---

def add_me_button(bot_username, style):
    return create_btn(
        text="『 𝐀ᴅᴅ 𝐌є 𝐁ᴀʙʏ 』",
        url=f"https://t.me/{bot_username}?startgroup=true",
        style=style
    )

def get_bar(played, dur):
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    total_blocks = 10
    filled_blocks = int((played_sec / duration_sec) * total_blocks) if duration_sec > 0 else 0
    bar = "▰" * filled_blocks + "▱" * (total_blocks - filled_blocks)
    return f"{played} {bar} {dur}"

# --- MARKUPS ---

def track_markup(_, videoid, user_id, channel, fplay):
    s_map = get_style_map()
    buttons = [
        [
            create_btn(text=_["P_B_1"], callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}", style=s_map[2]),
            create_btn(text=_["P_B_2"], callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}", style=s_map[2]),
        ],
        [create_btn(text=_["CLOSE_BUTTON"], callback_data=f"forceclose {videoid}|{user_id}", style=s_map[1])],
    ]
    return buttons

def stream_markup_timer(_, chat_id, played, dur):
    s_map = get_style_map()
    buttons = [
        [create_btn(text=get_bar(played, dur), callback_data="GetTimer", style=ButtonStyle.TRANSPARENT, no_emoji=True)],
        [
            create_btn(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style=s_map[3], no_emoji=True),
            create_btn(text="II", callback_data=f"ADMIN Pause|{chat_id}", style=s_map[3], no_emoji=True),
            create_btn(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=s_map[3], no_emoji=True),
        ],
        [create_btn(text="❖ 𝐀ᴜᴛᴏ𝐏ʟᴀʏ ❖", callback_data=f"ADMIN Autoplay|{chat_id}", style=s_map[1])],
        [create_btn(text=_["CLOSE_BUTTON"], callback_data="close", style=s_map[1])]
    ]
    return buttons

def stream_markup(_, chat_id):
    s_map = get_style_map()
    buttons = [
        [
            create_btn(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style=s_map[3], no_emoji=True),
            create_btn(text="II", callback_data=f"ADMIN Pause|{chat_id}", style=s_map[3], no_emoji=True),
            create_btn(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=s_map[3], no_emoji=True),
        ],
        [create_btn(text="❖ 𝐀ᴜᴛᴏ𝐏ʟᴀʏ ❖", callback_data=f"ADMIN Autoplay|{chat_id}", style=s_map[1])],
        [create_btn(text=_["CLOSE_BUTTON"], callback_data="close", style=s_map[1])]
    ]
    return buttons

def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    s_map = get_style_map()
    buttons = [
        [
            create_btn(text=_["P_B_1"], callback_data=f"ANJALIPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}", style=s_map[2]),
            create_btn(text=_["P_B_2"], callback_data=f"ANJALIPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}", style=s_map[2]),
        ],
        [create_btn(text=_["CLOSE_BUTTON"], callback_data=f"forceclose {videoid}|{user_id}", style=s_map[1])],
    ]
    return buttons

def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    s_map = get_style_map()
    buttons = [
        [create_btn(text=_["P_B_3"], callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}", style=s_map[1])],
        [create_btn(text=_["CLOSE_BUTTON"], callback_data=f"forceclose {videoid}|{user_id}", style=s_map[1])],
    ]
    return buttons

def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    query = f"{query[:20]}"
    s_map = get_style_map()
    buttons = [
        [
            create_btn(text=_["P_B_1"], callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}", style=s_map[2]),
            create_btn(text=_["P_B_2"], callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}", style=s_map[2]),
        ],
        [
            create_btn(text="◁", callback_data=f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}", style=s_map[3], no_emoji=True),
            create_btn(text=_["CLOSE_BUTTON"], callback_data=f"forceclose {query}|{user_id}", style=s_map[3]),
            create_btn(text="▷", callback_data=f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}", style=s_map[3], no_emoji=True),
        ],
    ]
    return buttons

def telegram_markup(_, chat_id):
    s_map = get_style_map()
    buttons = [
        [
            create_btn(text="Next", callback_data=f"PanelMarkup None|{chat_id}", style=s_map[2]),
            create_btn(text=_["CLOSEMENU_BUTTON"], callback_data="close", style=s_map[2]),
        ],
        [create_btn(text="❖ 𝐀ᴜᴛᴏ𝐏ʟᴀʏ ❖", callback_data=f"ADMIN Autoplay|{chat_id}", style=s_map[1])],
    ]
    return buttons

def queue_markup(_, videoid, chat_id, bot_username):
    s_map = get_style_map()
    buttons = [
        [add_me_button(bot_username, s_map[1])],
        [
            create_btn(text="II ᴘᴀᴜsᴇ", callback_data=f"ADMIN Pause|{chat_id}", style=s_map[3], no_emoji=True),
            create_btn(text="▢ sᴛᴏᴘ", callback_data=f"ADMIN Stop|{chat_id}", style=s_map[3], no_emoji=True),
            create_btn(text="sᴋɪᴘ ‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=s_map[3], no_emoji=True),
        ],
        [
            create_btn(text="▷ ʀᴇsᴜᴍᴇ", callback_data=f"ADMIN Resume|{chat_id}", style=s_map[2], no_emoji=True),
            create_btn(text="ʀᴇᴘʟᴀʏ ↺", callback_data=f"ADMIN Replay|{chat_id}", style=s_map[2], no_emoji=True),
        ],
        [create_btn(text="❖ 𝐀ᴜᴛᴏ𝐏ʟᴀʏ ❖", callback_data=f"ADMIN Autoplay|{chat_id}", style=s_map[1])],
        [create_btn(text="ᴍᴏʀᴇ", callback_data=f"PanelMarkup None|{chat_id}", style=s_map[1])],
    ]
    return buttons

def stream_markup2(_, chat_id, bot_username):
    s_map = get_style_map()
    buttons = [
        [add_me_button(bot_username, s_map[1])],
        [
            create_btn(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style=s_map[3], no_emoji=True),
            create_btn(text="II", callback_data=f"ADMIN Pause|{chat_id}", style=s_map[3], no_emoji=True),
            create_btn(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=s_map[3], no_emoji=True),
        ],
        [create_btn(text="❖ 𝐀ᴜᴛᴏ𝐏ʟᴀʏ ❖", callback_data=f"ADMIN Autoplay|{chat_id}", style=s_map[1])],
        [create_btn(text=_["CLOSEMENU_BUTTON"], callback_data="close", style=s_map[1])],
    ]
    return buttons

def stream_markup_timer2(_, chat_id, played, dur):
    s_map = get_style_map()
    buttons = [
        [create_btn(text=get_bar(played, dur), callback_data="GetTimer", style=ButtonStyle.TRANSPARENT, no_emoji=True)],
        [
            create_btn(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style=s_map[3], no_emoji=True),
            create_btn(text="II", callback_data=f"ADMIN Pause|{chat_id}", style=s_map[3], no_emoji=True),
            create_btn(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=s_map[3], no_emoji=True),
        ],
        [create_btn(text="❖ 𝐀ᴜᴛᴏ𝐏ʟᴀʏ ❖", callback_data=f"ADMIN Autoplay|{chat_id}", style=s_map[1])],
        [create_btn(text=_["CLOSEMENU_BUTTON"], callback_data="close", style=s_map[1])],
    ]
    return buttons

def panel_markup_1(_, videoid, chat_id, bot_username):
    s_map = get_style_map()
    buttons = [
        [add_me_button(bot_username, s_map[1])],
        [
            create_btn(text="sᴜғғʟᴇ", callback_data=f"ADMIN Shuffle|{chat_id}", style=s_map[2], no_emoji=True),
            create_btn(text="ʟᴏᴏᴘ ↺", callback_data=f"ADMIN Loop|{chat_id}", style=s_map[2], no_emoji=True),
        ],
        [
            create_btn(text="◁ 10 sᴇᴄ", callback_data=f"ADMIN 1|{chat_id}", style=s_map[2], no_emoji=True),
            create_btn(text="10 sᴇᴄ ▷", callback_data=f"ADMIN 2|{chat_id}", style=s_map[2], no_emoji=True),
        ],
        [create_btn(text="❖ 𝐀ᴜᴛᴏ𝐏ʟᴀʏ ❖", callback_data=f"ADMIN Autoplay|{chat_id}", style=s_map[1])],
        [
            create_btn(text="ʜᴏᴍᴇ", callback_data=f"Pages Back|2|{videoid}|{chat_id}", style=s_map[2], no_emoji=True),
            create_btn(text="ɴᴇxᴛ", callback_data=f"Pages Forw|2|{videoid}|{chat_id}", style=s_map[2], no_emoji=True),
        ],
    ]
    return buttons

def panel_markup_2(_, videoid, chat_id, bot_username):
    s_map = get_style_map()
    buttons = [
        [add_me_button(bot_username, s_map[1])],
        [
            create_btn(text="🕒 0.5x", callback_data=f"SpeedUP {chat_id}|0.5", style=s_map[3], no_emoji=True),
            create_btn(text="🕓 0.75x", callback_data=f"SpeedUP {chat_id}|0.75", style=s_map[3], no_emoji=True),
            create_btn(text="🕤 1.0x", callback_data=f"SpeedUP {chat_id}|1.0", style=s_map[3], no_emoji=True),
        ],
        [
            create_btn(text="🕤 1.5x", callback_data=f"SpeedUP {chat_id}|1.5", style=s_map[2], no_emoji=True),
            create_btn(text="🕛 2.0x", callback_data=f"SpeedUP {chat_id}|2.0", style=s_map[2], no_emoji=True),
        ],
        [create_btn(text="❖ 𝐀ᴜᴛᴏ𝐏ʟᴀʏ ❖", callback_data=f"ADMIN Autoplay|{chat_id}", style=s_map[1])],
        [create_btn(text="ʙᴀᴄᴋ", callback_data=f"Pages Back|1|{videoid}|{chat_id}", style=s_map[1], no_emoji=True)],
    ]
    return buttons

def panel_markup_3(_, videoid, chat_id):
    s_map = get_style_map()
    buttons = [
        [
            create_btn(text="🕒 0.5x", callback_data=f"SpeedUP {chat_id}|0.5", style=s_map[3], no_emoji=True),
            create_btn(text="🕓 0.75x", callback_data=f"SpeedUP {chat_id}|0.75", style=s_map[3], no_emoji=True),
            create_btn(text="🕤 1.0x", callback_data=f"SpeedUP {chat_id}|1.0", style=s_map[3], no_emoji=True),
        ],
        [
            create_btn(text="🕤 1.5x", callback_data=f"SpeedUP {chat_id}|1.5", style=s_map[2], no_emoji=True),
            create_btn(text="🕛 2.0x", callback_data=f"SpeedUP {chat_id}|2.0", style=s_map[2], no_emoji=True),
        ],
        [create_btn(text="❖ 𝐀ᴜᴛᴏ𝐏ʟᴀʏ ❖", callback_data=f"ADMIN Autoplay|{chat_id}", style=s_map[1])],
        [create_btn(text="ʙᴀᴄᴋ", callback_data=f"Pages Back|2|{videoid}|{chat_id}", style=s_map[1], no_emoji=True)],
    ]
    return buttons

def panel_markup_4(_, vidid, chat_id, played, dur):
    s_map = get_style_map()
    buttons = [
        [create_btn(text=get_bar(played, dur), callback_data="GetTimer", style=ButtonStyle.TRANSPARENT, no_emoji=True)],
        [
            create_btn(text="II ᴘᴀᴜsᴇ", callback_data=f"ADMIN Pause|{chat_id}", style=s_map[3], no_emoji=True),
            create_btn(text="▢ sᴛᴏᴘ ▢", callback_data=f"ADMIN Stop|{chat_id}", style=s_map[3], no_emoji=True),
            create_btn(text="sᴋɪᴘ ‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=s_map[3], no_emoji=True),
        ],
        [create_btn(text="▷ ʀᴇsᴜᴍᴇ", callback_data=f"ADMIN Resume|{chat_id}", style=s_map[1], no_emoji=True)],
        [create_btn(text="❖ 𝐀ᴜᴛᴏ𝐏ʟᴀʏ ❖", callback_data=f"ADMIN Autoplay|{chat_id}", style=s_map[1])],
        [create_btn(text="ʜᴏᴍᴇ", callback_data=f"MainMarkup {vidid}|{chat_id}", style=s_map[1], no_emoji=True)],
    ]
    return buttons

def panel_markup_5(_, videoid, chat_id, bot_username):
    s_map = get_style_map()
    buttons = [
        [add_me_button(bot_username, s_map[1])],
        [
            create_btn(text="ᴘᴀᴜsᴇ", callback_data=f"ADMIN Pause|{chat_id}", style=s_map[3], no_emoji=True),
            create_btn(text="sᴛᴏᴘ", callback_data=f"ADMIN Stop|{chat_id}", style=s_map[3], no_emoji=True),
            create_btn(text="sᴋɪᴘ", callback_data=f"ADMIN Skip|{chat_id}", style=s_map[3], no_emoji=True),
        ],
        [
            create_btn(text="ʀᴇsᴜᴍᴇ", callback_data=f"ADMIN Resume|{chat_id}", style=s_map[2], no_emoji=True),
            create_btn(text="ʀᴇᴘʟᴀʏ", callback_data=f"ADMIN Replay|{chat_id}", style=s_map[2], no_emoji=True),
        ],
        [create_btn(text="❖ 𝐀ᴜᴛᴏ𝐏ʟᴀʏ ❖", callback_data=f"ADMIN Autoplay|{chat_id}", style=s_map[1])],
        [
            create_btn(text="ʜᴏᴍᴇ", callback_data=f"MainMarkup {videoid}|{chat_id}", style=s_map[2], no_emoji=True),
            create_btn(text="ɴᴇxᴛ", callback_data=f"Pages Forw|1|{videoid}|{chat_id}", style=s_map[2], no_emoji=True),
        ],
    ]
    return buttons

def panel_markup_clone(_, vidid, chat_id, premium=True, **kwargs):
    s_map = get_style_map()
    buttons = [
        [
            create_btn(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style=s_map[3], no_emoji=True),
            create_btn(text="II", callback_data=f"ADMIN Pause|{chat_id}", style=s_map[3], no_emoji=True),
            create_btn(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=s_map[3], no_emoji=True),
        ],
        [
            create_btn(text="<- 20s", callback_data=f"ADMIN SeekBack|{chat_id}", style=s_map[4], no_emoji=True),
            create_btn(text="🔁", callback_data=f"ADMIN Loop|{chat_id}", style=s_map[4], no_emoji=True),
            create_btn(text="🔀", callback_data=f"ADMIN Shuffle|{chat_id}", style=s_map[4], no_emoji=True),
            create_btn(text="20s + ->", callback_data=f"ADMIN SeekForward|{chat_id}", style=s_map[4], no_emoji=True),
        ],
        [create_btn(text=_["CLOSE_BUTTON"], callback_data="close", style=s_map[1], no_emoji=True)]
    ]
    return buttons
