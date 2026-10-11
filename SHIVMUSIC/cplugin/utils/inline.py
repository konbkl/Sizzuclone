from pyrogram.types import InlineKeyboardMarkup
from button import styled_button, ButtonStyle # Zaroori import

# --- OPTION 1: Static ---
buttons = InlineKeyboardMarkup(
    [
        [
            styled_button(text="▷", callback_data="resume_cb", style=ButtonStyle.SUCCESS),
            styled_button(text="II", callback_data="pause_cb", style=ButtonStyle.DANGER),
            styled_button(text="‣‣I", callback_data="skip_cb", style=ButtonStyle.PRIMARY),
            styled_button(text="▢", callback_data="end_cb", style=ButtonStyle.DANGER),
        ],
        [
            styled_button(text="『 ✦ 𝐂ʟᴏηє 𝐌є ✦ 』", url="https://t.me/SizzuMusicBot", style=ButtonStyle.SUCCESS)
        ],
    ]
)

close_key = InlineKeyboardMarkup(
    [
        # "Add me" hata diya gaya hai, ab sirf Close bacha hai
        [
            styled_button(text="✯ CLOSE ✯", callback_data="close", style=ButtonStyle.DANGER)
        ]
    ]
)

# --- OPTION 2: Dynamic (RECOMMENDED) ---
def stream_markup(chat_id):
    return InlineKeyboardMarkup(
        [
            # Top Row: Basic Controls
            [
                styled_button(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style=ButtonStyle.SUCCESS),
                styled_button(text="II", callback_data=f"ADMIN Pause|{chat_id}", style=ButtonStyle.DANGER),
                styled_button(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=ButtonStyle.PRIMARY),
                styled_button(text="▢", callback_data=f"ADMIN Stop|{chat_id}", style=ButtonStyle.DANGER),
            ],
            # Middle Row: Seek Buttons
            [
                styled_button(text="<- 20s", callback_data=f"ADMIN SeekBack|{chat_id}", style=ButtonStyle.PRIMARY),
                styled_button(text="20s + ->", callback_data=f"ADMIN SeekForward|{chat_id}", style=ButtonStyle.PRIMARY),
            ],
            # Bottom Row: Clone & Close merged (Space bachane ke liye!)
            [
                styled_button(text="『 ✦ 𝐂ʟᴏηє 𝐌є ✦ 』", url="https://t.me/SizzuMusicBot", style=ButtonStyle.SUCCESS),
                styled_button(text="✯ CLOSE ✯", callback_data="close", style=ButtonStyle.DANGER)
            ]
        ]
    )
    
