import os
import uuid
import asyncio
import random
import time
from datetime import datetime
from typing import Union
import re
import unicodedata
import urllib.parse
from urllib.parse import urlparse

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InputMediaPhoto, Message, InlineKeyboardButton
from pyrogram.errors import MessageIdInvalid, MessageNotModified
from pytgcalls.exceptions import NoActiveGroupCall

import config
from SHIVMUSIC import Apple, Resso, SoundCloud, Spotify, Telegram, YouTube, app, LOGGER
from SHIVMUSIC.core.call import ANJALI
from SHIVMUSIC.misc import SUDOERS, db

from SHIVMUSIC.cplugin.buttons import (
    livestream_markup,
    playlist_markup,
    slider_markup,
    track_markup,
    queue_markup,
    stream_markup,
    stream_markup_timer,
    stream_markup2,
    stream_markup_timer2,
    panel_markup_1,
    panel_markup_2,
    panel_markup_3,
    panel_markup_4,
    panel_markup_5,
    panel_markup_clone,
    telegram_markup
)

from SHIVMUSIC.utils import seconds_to_min, time_to_seconds
from SHIVMUSIC.utils.channelplay import get_channeplayCB
from SHIVMUSIC.utils.decorators.language import languageCB
from SHIVMUSIC.utils.decorators.play import CPlayWrapper
from SHIVMUSIC.utils.formatters import formats
from SHIVMUSIC.utils.inline import close_markup, aq_markup
from SHIVMUSIC.utils.database import get_assistant

from SHIVMUSIC.utils.database import (
    add_served_user_clone,
    is_active_chat,
    add_active_video_chat,
    remove_active_chat,
    remove_active_video_chat,
    clonebotdb
)

from SHIVMUSIC.utils.database.clonedb import (
    get_owner_id_from_db, 
    get_cloned_support_chat, 
    get_clone_search_settings,
    get_clone_stream_caption
)

from SHIVMUSIC.utils.exceptions import AssistantErr
from SHIVMUSIC.utils.pastebin import ANJALIBin
from SHIVMUSIC.utils.stream.queue import put_queue, put_queue_index
from SHIVMUSIC.utils.logger import play_logs, clone_bot_logs
from SHIVMUSIC.cplugin.setinfo import get_logging_status, get_log_channel
from SHIVMUSIC.cplugin.utils.cthumbnail import get_thumb

from config import BANNED_USERS, lyrical

# =======================================================
# 🎨 PREMIUM TEXT STYLES (BETA HUB)
# =======================================================
MSG_DOWNLOADING = "<tg-emoji emoji-id=\"6156513311585211842\">🌀</tg-emoji> 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝐅𝐫𝐨𝐦 𝐁𝐞𝐭𝐚 𝐇𝐮𝐛 𝐁𝐚𝐛𝐲 𝐩𝐥𝐞𝐚𝐬𝐞 𝐰𝐚𝐢𝐭...."
MSG_STARTING = "<tg-emoji emoji-id=\"6129476453802188018\">▶️</tg-emoji> 𝐒𝐭𝐚𝐫𝐭𝐢𝐧𝐠 𝐒𝐭𝐫𝐞𝐚𝐦 𝐄𝐧𝐣𝐨𝐲...."

# ✨ NEW ATTRACTIVE VC OFF MESSAGE (BOLD & QUOTE FORMAT)
VC_OFF_MSG = (
    "> **<tg-emoji emoji-id=\"6129782440157256336\">🥹</tg-emoji> ᴏᴏᴘs! ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ɪs ᴏғғ...**\n"
    "> \n"
    "> **<tg-emoji emoji-id=\"5294339927318739359\">🎙️</tg-emoji> ᴘʟᴇᴀsᴇ ᴛᴜʀɴ ᴏɴ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ sᴏ ɪ ᴄᴀɴ ᴘʟᴀʏ sᴏᴍᴇ ᴀᴡᴇsᴏᴍᴇ ᴍᴜsɪᴄ ғᴏʀ ʏᴏᴜ! <tg-emoji emoji-id=\"6098202009486233047\">🥳</tg-emoji>**"
)

def is_vc_off(e):
    try:
        ex_str = str(e).lower()
        ex_name = type(e).__name__.lower()
        # ✨ FIXED: Assistant permission error (chat_admin_required) is also handled
        vc_errors = [
            "noactivegroupcall",
            "groupcallnotfound",
            "chat_admin_required",
            "creategroupcall",
            "voice chat is turned on"
        ]
        if any(err in ex_str for err in vc_errors) or any(err in ex_name for err in vc_errors):
            return True
        return False
    except:
        return False

# =======================================================
# 🚀 STYLISH LIVE PROGRESS BAR
# =======================================================
EDIT_TIME = {}

async def stylish_progress_bar(current, total, msg, start_time):
    if total == 0:
        return
        
    now = time.time()
    if msg.id in EDIT_TIME:
        if now - EDIT_TIME[msg.id] < 2.0:
            return
    EDIT_TIME[msg.id] = now

    percentage = current * 100 / total
    downloaded = round(current / (1024 * 1024), 2)
    total_size = round(total / (1024 * 1024), 2)
    speed = round(downloaded / (now - start_time), 2) if (now - start_time) > 0 else 0
    eta = round((total - current) / (speed * 1024 * 1024)) if speed > 0 else 0

    filled = int(percentage / 10)
    empty = 10 - filled
    bar = "▰" * filled + "▱" * empty

    text = f"**{MSG_DOWNLOADING}**\n\n"
    text += f"<tg-emoji emoji-id=\"6100220081474639964\">⚡</tg-emoji> **𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬:** `[{bar}] {round(percentage, 2)}%`\n"
    text += f"<tg-emoji emoji-id=\"5409186957676785646\">📥</tg-emoji> **𝐒𝐢𝐳𝐞:** `{downloaded} MB / {total_size} MB`\n"
    text += f"<tg-emoji emoji-id=\"6172332822892647766\">🚀</tg-emoji> **𝐒𝐩𝐞𝐞𝐝:** `{speed} MB/s`\n"
    text += f"<tg-emoji emoji-id=\"5891211339170326418\">⏳</tg-emoji> **𝐄𝐓𝐀:** `{eta} sec`\n"

    try:
        await msg.edit_text(text)
    except Exception:
        pass


user_last_message_time = {}
user_command_count = {}
SPAM_THRESHOLD = 2
SPAM_WINDOW_SECONDS = 5

# =======================================================
# 🛡️ BULLETPROOF SECURITY & ANTI-RCE WALL
# =======================================================
BANNED_WORDS = [
    "porn", "pornhub", "xvideos", "xnxx", "brazzers", 
    "onlyfans", "xhamster", "hot bhabhi", "deskbabe", "redtube", "spankbang",
    "child porn", "pedophile", "pedo", "jailbait", "loli", "shota", "csam",
    "incest", "bestiality", "zoophilia", "snuff", "revenge porn", "nonconsensual", "Webhook.site"
]

def clean_invisible_chars(text):
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize('NFKC', text)
    return re.sub(r'[\u200B-\u200D\uFEFF\u202A-\u202E\u200e\u200f]', '', text)

def is_nsfw_content(text):
    if not text:
        return False
    text = urllib.parse.unquote(str(text)).lower()
    text = clean_invisible_chars(text)
    for word in BANNED_WORDS:
        if re.search(r'\b' + re.escape(word) + r'\b', text):
            return True
    return False

def is_malicious_link(text):
    if not text:
        return False
    
    decoded_text = urllib.parse.unquote(str(text)).lower()
    clean_text = clean_invisible_chars(decoded_text)
    
    suspicious_chars = re.compile(r'[;|&$`{}<>\\]')
    if suspicious_chars.search(clean_text):
        return True

    if re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', clean_text): return True
    bad_extensions = ["webhook", "ngrok", "localhost", "0.0.0.0", ".sh", ".txt", "payload", ".exe", ".bat", ".vbs", ".cmd", ".py", ".php"]
    if any(ext in clean_text for ext in bad_extensions): return True
    
    dangerous_chars = ["rm -rf", "wget ", "curl ", "chmod ", "bash -c", "eval(", "tar ", "cp ", "/proc/self", "ifs", "env.txt"]
    if any(char in clean_text for char in dangerous_chars): return True
    
    return False

def bouncer_check(_, __, message: Message):
    if not message.text: return True
    
    decoded_text = urllib.parse.unquote(message.text).lower()
    clean_text = clean_invisible_chars(decoded_text)
    
    suspicious_chars = re.compile(r'[;|&$`{}<>\\]')
    if suspicious_chars.search(clean_text): return False
    
    dangerous_symbols = ["ifs", "/etc/passwd", ".env", "webhook.site", "rm -rf", "wget ", "curl ", "chmod ", "bash -c", "eval(", "tar ", "cp ", "env.txt"]
    if any(sym in clean_text for sym in dangerous_symbols): return False 
    
    return True

god_mode_filter = filters.create(bouncer_check)
# =======================================================

async def send_security_log(message: Message, breach_type: str, payload: str):
    try:
        chat_id = message.chat.id
        chat_title = message.chat.title
        user_mention = message.from_user.mention
        user_id = message.from_user.id

        log_text = (
            f"<tg-emoji emoji-id=\"6102938383456146362\">🚨</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: {breach_type}**\n\n"
            f"<tg-emoji emoji-id=\"6032609071373226027\">👤</tg-emoji> **ᴜsᴇʀ:** {user_mention} (`{user_id}`)\n"
            f"<tg-emoji emoji-id=\"6100424015111787987\">🏠</tg-emoji> **ᴄʜᴀᴛ:** {chat_title} (`{chat_id}`)\n"
            f"<tg-emoji emoji-id=\"6102938383456146362\">⚠️</tg-emoji> **ᴘᴀʏʟᴏᴀᴅ:** `{payload}`"
        )
        await app.send_message(config.LOGGER_ID, text=log_text)
    except Exception:
        pass

def get_random_img(img_list):
    if img_list:
        if isinstance(img_list, list):
            return random.choice(img_list)
        return img_list
    return "https://telegra.ph/file/2e3d368e77c449c287430.jpg"

def clean_youtube_url(url):
    if not isinstance(url, str): return url, None, "unknown"
    list_match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
    if list_match and ("youtube.com" in url or "youtu.be" in url):
        return f"https://www.youtube.com/playlist?list={list_match.group(1)}", list_match.group(1), "playlist"
    yt_match = re.search(r"(?:v=|youtu\.be/|shorts/|live/|embed/|watch\?v=|music\.youtube\.com/watch\?v=|/v/)([a-zA-Z0-9_-]{11})", url)
    if yt_match:
        return f"https://www.youtube.com/watch?v={yt_match.group(1)}", yt_match.group(1), "video"
    return url, None, "unknown"


async def update_clone_activity(username):
    try:
        if username:
            await clonebotdb.update_one(
                {"username": username},
                {"$set": {"last_activity": datetime.now()}}
            )
    except:
        pass

@Client.on_message(
    filters.command(
        [
            "play", "vplay", "cplay", "cvplay", "playforce", "vplayforce", "cplayforce", "cvplayforce"
        ],
        prefixes=["/", "!", "%", ".", "@", "#"], 
    )
    & filters.group
    & ~BANNED_USERS
    & god_mode_filter 
)
@CPlayWrapper
async def play_commnd(client, message: Message, _, chat_id, video, channel, playmode, url, fplay):
    cuser = await client.get_me()
    asyncio.create_task(update_clone_activity(cuser.username))
    asyncio.create_task(add_served_user_clone(message.chat.id, cuser.id))

    bot_id = cuser.id
    user_id = message.from_user.id

    userbot = None
    use_global_assistant = False

    if hasattr(client, "assistant") and client.assistant:
        try:
            if not client.assistant.is_connected:
                await client.assistant.start()
            
            await client.assistant.get_me()
            userbot = client.assistant
        except Exception as e:
            try:
                await clonebotdb.update_one(
                    {"bot_id": client.me.id},
                    {"$unset": {"session": 1}}
                )
            except:
                pass

            try:
                db[chat_id] = []
                await remove_active_chat(chat_id)
                await remove_active_video_chat(chat_id)
            except:
                pass
            
            client.assistant = None
            use_global_assistant = True
            userbot = None
    else:
        use_global_assistant = True

    tasks = [
        get_owner_id_from_db(bot_id),
        get_logging_status(bot_id),
        get_log_channel(bot_id),
        get_clone_search_settings(bot_id)
    ]

    if use_global_assistant:
        tasks.append(get_assistant(chat_id))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    C_BOT_OWNER_ID = results[0]
    C_LOG_STATUS = results[1] if not isinstance(results[1], Exception) else True
    C_LOGGER_ID = results[2]
    
    search_settings = results[3]
    stype, scontent = search_settings if not isinstance(search_settings, Exception) else ("text", None)

    if use_global_assistant:
        userbot = results[4]

    bot_mention = cuser.mention
    
    if str(C_LOGGER_ID) == "-100" or isinstance(C_LOGGER_ID, Exception):
        C_LOGGER_ID = C_BOT_OWNER_ID
    clone_logger_id = C_LOGGER_ID

    current_time = time.time()
    last_message_time = user_last_message_time.get(user_id, 0)
    if current_time - last_message_time < SPAM_WINDOW_SECONDS:
        user_last_message_time[user_id] = current_time
        user_command_count[user_id] = user_command_count.get(user_id, 0) + 1
        if user_command_count[user_id] > SPAM_THRESHOLD:
            hu = await message.reply_text(f"<tg-emoji emoji-id=\"6102938383456146362\">⚠️</tg-emoji> **{message.from_user.mention} ᴘʟᴇᴀsᴇ ᴅᴏ ɴᴏᴛ sᴘᴀᴍ. ᴛʀʏ ᴀɢᴀɪɴ ɪɴ 5 sᴇᴄᴏɴᴅs.**")
            await asyncio.sleep(3)
            return await hu.delete()
    else:
        user_command_count[user_id] = 1
        user_last_message_time[user_id] = current_time
    
    try:
        if stype == "text" and scontent:
            mystic = await message.reply_text(scontent)
        elif stype == "sticker" and scontent:
            mystic = await message.reply_sticker(scontent)
        elif stype == "animation" and scontent:
            mystic = await message.reply_animation(scontent)
        elif stype == "video" and scontent:
            mystic = await message.reply_video(scontent)
        elif stype == "photo" and scontent:
            mystic = await message.reply_photo(scontent)
        else:
            mystic = await message.reply_text(MSG_DOWNLOADING)
    except:
        mystic = await message.reply_text(MSG_DOWNLOADING)

    plist_id = None
    slider = None
    plist_type = None
    spotify = None
    user_name = message.from_user.mention

    audio_telegram = ((message.reply_to_message.audio or message.reply_to_message.voice) if message.reply_to_message else None)
    video_telegram = ((message.reply_to_message.video or message.reply_to_message.document) if message.reply_to_message else None)
    
    # ===========================================================
    # 🎵 AUDIO LOCAL PLAY HANDLER (UP TO 4GB)
    # ===========================================================
    if audio_telegram:
        if audio_telegram.file_size > 4294967296: # 4GB Limit
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **File is too large! Maximum allowed limit is 4GB.**")
            
        duration_min = seconds_to_min(audio_telegram.duration) if hasattr(audio_telegram, 'duration') and audio_telegram.duration else "Unknown"
        
        dl_client = client
        msg_to_dl = message.reply_to_message
        
        if audio_telegram.file_size > 20971520: # 20 MB limit switch
            if not userbot:
                return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Assistant Required!**\nTo play files larger than 20MB, the assistant account must be active.")
            dl_client = userbot
            try:
                msg_to_dl = await userbot.get_messages(message.chat.id, message.reply_to_message.id)
            except Exception as e:
                return await mystic.edit_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Assistant Access Error:** `{e}`")

        try:
            start_time = time.time()
            file_path = await dl_client.download_media(
                msg_to_dl,
                file_name="downloads/",
                progress=stylish_progress_bar,
                progress_args=(mystic, start_time)
            )
        except Exception as e:
            return await mystic.edit_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Download Error:** `{e}`")

        if file_path and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            message_link = await Telegram.get_link(message)
            file_name = audio_telegram.file_name if hasattr(audio_telegram, 'file_name') else "Audio File"
            dur = await Telegram.get_duration(audio_telegram, file_path)
            details = {"title": file_name, "link": message_link, "path": file_path, "dur": dur}
            
            if is_nsfw_content(details.get("title", "")):
                await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ (Telegram Audio)", details.get("title", ""))
                return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

            try:
                if getattr(mystic, "text", None):
                    await mystic.edit_text(MSG_STARTING)
                    pass  # no delay
            except: pass

            try:
                await stream(client, _, mystic, user_id, details, chat_id, user_name, message.chat.id, streamtype="telegram", forceplay=fplay, userbot=userbot)
            except Exception as e:
                if is_vc_off(e):
                    try:
                        return await mystic.edit_text(VC_OFF_MSG)
                    except MessageIdInvalid:
                        return await message.reply_text(VC_OFF_MSG)
                print(e)
                try:
                    return await mystic.edit_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **sᴛʀᴇᴀᴍ ᴇʀʀᴏʀ (ᴀᴜᴅɪᴏ):**\n\n`{str(e)}`")
                except MessageIdInvalid:
                    return await message.reply_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **sᴛʀᴇᴀᴍ ᴇʀʀᴏʀ:** `{str(e)}`")
                except MessageNotModified:
                    return
            return await mystic.delete()
        else:
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Download Failed:** The file is empty or corrupted.")

    # ===========================================================
    # 🎥 VIDEO LOCAL PLAY HANDLER (UP TO 4GB)
    # ===========================================================
    elif video_telegram:
        if message.reply_to_message.document:
            try:
                ext = video_telegram.file_name.split(".")[-1]
                if ext.lower() not in formats:
                    return await mystic.edit_text(_["play_7"].format(f"{' | '.join(formats)}"))
            except:
                pass
                
        if video_telegram.file_size > 4294967296: # 4GB Limit
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **File is too large! Maximum allowed limit is 4GB.**")
            
        dl_client = client
        msg_to_dl = message.reply_to_message
        
        if video_telegram.file_size > 20971520: # 20 MB limit switch
            if not userbot:
                return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Assistant Required!**\nTo play files larger than 20MB, the assistant account must be active.")
            dl_client = userbot
            try:
                msg_to_dl = await userbot.get_messages(message.chat.id, message.reply_to_message.id)
            except Exception as e:
                return await mystic.edit_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Assistant Access Error:** `{e}`")

        try:
            start_time = time.time()
            file_path = await dl_client.download_media(
                msg_to_dl,
                file_name="downloads/",
                progress=stylish_progress_bar,
                progress_args=(mystic, start_time)
            )
        except Exception as e:
            return await mystic.edit_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Download Error:** `{e}`")

        if file_path and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            message_link = await Telegram.get_link(message)
            file_name = video_telegram.file_name if hasattr(video_telegram, 'file_name') else "Video File"
            dur = await Telegram.get_duration(video_telegram, file_path)
            details = {"title": file_name, "link": message_link, "path": file_path, "dur": dur}
            
            if is_nsfw_content(details.get("title", "")):
                await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ (Telegram Video)", details.get("title", ""))
                return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

            try:
                if getattr(mystic, "text", None):
                    await mystic.edit_text(MSG_STARTING)
                    pass  # no delay
            except: pass

            try:
                await stream(client, _, mystic, user_id, details, chat_id, user_name, message.chat.id, video=True, streamtype="telegram", forceplay=fplay, userbot=userbot)
            except Exception as e:
                if is_vc_off(e):
                    try:
                        return await mystic.edit_text(VC_OFF_MSG)
                    except MessageIdInvalid:
                        return await message.reply_text(VC_OFF_MSG)
                print(e)
                try:
                    return await mystic.edit_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **sᴛʀᴇᴀᴍ ᴇʀʀᴏʀ (ᴠɪᴅᴇᴏ):**\n\n`{str(e)}`")
                except MessageIdInvalid:
                    return await message.reply_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **sᴛʀᴇᴀᴍ ᴇʀʀᴏʀ:** `{str(e)}`")
                except MessageNotModified:
                    return
            return await mystic.delete()
        else:
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Download Failed!** The file is empty.\n\n_Note: Ensure the Assistant account is a Premium account if downloading files up to 4GB._")
    
    # ===========================================================
    # 🌐 URL HANDLER
    # ===========================================================
    elif url:
        if not url.startswith(("http://", "https://")):
             return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴇʀʀᴏʀ:** ʟᴏᴄᴀʟ ғɪʟᴇs ᴀʀᴇ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ ᴛᴏ ᴘʀᴇᴠᴇɴᴛ ᴅᴀᴛᴀ ᴛʜᴇғᴛ.")

        if is_malicious_link(url):
            await send_security_log(message, "ᴍᴀʟɪᴄɪᴏᴜs ʜᴀᴄᴋ ʟɪɴᴋ ʙʟᴏᴄᴋᴇᴅ", url)
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴍᴀʟɪᴄɪᴏᴜs ᴄᴏᴍᴍᴀɴᴅ ɪɴᴊᴇᴄᴛɪᴏɴ ʙʟᴏᴄᴋᴇᴅ!**")

        if is_nsfw_content(url):
            await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", url)
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

        allowed_domains = [
            "youtube.com", "youtu.be",
            "spotify.com", 
            "soundcloud.com",
            "music.apple.com", 
            "resso.com"
        ]
        
        if not any(domain in url for domain in allowed_domains):
             return await mystic.edit_text(
                 "<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **ᴜɴsᴜᴘᴘᴏʀᴛᴇᴅ ʟɪɴᴋ!**\n\n"
                 "**ᴀʟʟᴏᴡᴇᴅ sᴏᴜʀᴄᴇs:** ʏᴏᴜᴛᴜʙᴇ, sᴘᴏᴛɪғʏ, sᴏᴜɴᴅᴄʟᴏᴜᴅ, ᴀᴘᴘʟᴇ ᴍᴜsɪᴄ, ʀᴇssᴏ.\n"
                 "**sᴇᴄᴜʀɪᴛʏ:** ᴏᴛʜᴇʀ ʟɪɴᴋs ᴀʀᴇ ʙʟᴏᴄᴋᴇᴅ ᴛᴏ ᴋᴇᴇᴘ ᴛʜᴇ sᴇʀᴠᴇʀ sᴀғᴇ."
             )

        if "spotify.com" in url:
            spotify = True
            if not config.SPOTIFY_CLIENT_ID and not config.SPOTIFY_CLIENT_SECRET:
                return await mystic.edit_text("<tg-emoji emoji-id=\"6172312314423808834\">✨</tg-emoji> sᴘᴏᴛɪғʏ ɪs ɴᴏᴛ sᴜᴘᴘᴏʀᴛᴇᴅ ʏᴇᴛ.")
            try:
                if "track" in url:
                    details, track_id = await Spotify.track(url)
                    streamtype = "youtube"
                    img = details["thumb"]
                    cap = _["play_10"].format(details["title"], details["duration_min"])
                elif "playlist" in url:
                    details, plist_id = await Spotify.playlist(url)
                    streamtype = "playlist"
                    plist_type = "spplay"
                    img = get_random_img(config.SPOTIFY_PLAYLIST_IMG_URL)
                    cap = _["play_11"].format(cuser.mention, message.from_user.mention)
                elif "album" in url:
                    details, plist_id = await Spotify.album(url)
                    streamtype = "playlist"
                    plist_type = "spalbum"
                    img = get_random_img(config.SPOTIFY_ALBUM_IMG_URL)
                    cap = _["play_11"].format(cuser.mention, message.from_user.mention)
                elif "artist" in url:
                    details, plist_id = await Spotify.artist(url)
                    streamtype = "playlist"
                    plist_type = "spartist"
                    img = get_random_img(config.SPOTIFY_ARTIST_IMG_URL)
                    cap = _["play_11"].format(message.from_user.first_name)
                else:
                    return await mystic.edit_text(_["play_15"])

                if is_nsfw_content(details.get("title", "")):
                    await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", details.get("title", ""))
                    return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")
            except:
                return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> ᴇʀʀᴏʀ ғᴇᴛᴄʜɪɴɢ sᴘᴏᴛɪғʏ ᴅᴀᴛᴀ.")
        
        elif "music.apple.com" in url:
            try:
                if "album" in url:
                    details, track_id = await Apple.track(url)
                    streamtype = "youtube"
                    img = details["thumb"]
                    cap = _["play_10"].format(details["title"], details["duration_min"])
                elif "playlist" in url:
                    spotify = True
                    details, plist_id = await Apple.playlist(url)
                    streamtype = "playlist"
                    plist_type = "apple"
                    cap = _["play_12"].format(cuser.mention, message.from_user.mention)
                    img = url
                else:
                    return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> ᴇʀʀᴏʀ: ɪɴᴠᴀʟɪᴅ ᴀᴘᴘʟᴇ ᴍᴜsɪᴄ ʟɪɴᴋ.")

                if is_nsfw_content(details.get("title", "")):
                    await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", details.get("title", ""))
                    return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")
            except:
                return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> ᴇʀʀᴏʀ ғᴇᴛᴄʜɪɴɢ ᴀᴘᴘʟᴇ ᴍᴜsɪᴄ.")

        elif "resso.com" in url:
            try:
                details, track_id = await Resso.track(url)
                
                if is_nsfw_content(details.get("title", "")):
                    await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", details.get("title", ""))
                    return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

                streamtype = "youtube"
                img = details["thumb"]
                cap = _["play_10"].format(details["title"], details["duration_min"])
            except:
                return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> ᴇʀʀᴏʀ ғᴇᴛᴄʜɪɴɢ ʀᴇssᴏ ᴛʀᴀᴄᴋ.")

        elif "soundcloud.com" in url:
            try:
                details, track_path = await SoundCloud.download(url)
                
                if is_nsfw_content(details.get("title", "")):
                    await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", details.get("title", ""))
                    return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

                duration_sec = details["duration_sec"]
                if duration_sec > config.DURATION_LIMIT:
                    return await mystic.edit_text(_["play_6"].format(config.DURATION_LIMIT_MIN, cuser.mention))
                
                try:
                    if getattr(mystic, "text", None):
                        await mystic.edit_text(MSG_STARTING)
                        pass  # no delay
                except: pass

                await stream(client, _, mystic, user_id, details, chat_id, user_name, message.chat.id, streamtype="soundcloud", forceplay=fplay, userbot=userbot)
                return await mystic.delete()
            except Exception as e:
                if is_vc_off(e):
                    try:
                        return await mystic.edit_text(VC_OFF_MSG)
                    except MessageIdInvalid:
                        return await message.reply_text(VC_OFF_MSG)
                return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> ᴇʀʀᴏʀ ғᴇᴛᴄʜɪɴɢ sᴏᴜɴᴅᴄʟᴏᴜᴅ.")

        else:
            try:
                clean_url, ext_id, y_type = clean_youtube_url(url)
                
                if y_type == "playlist":
                    details = await YouTube.playlist(clean_url, config.PLAYLIST_FETCH_LIMIT, message.from_user.id)
                    streamtype = "playlist"
                    plist_type = "yt"
                    plist_id = ext_id
                    img = get_random_img(config.PLAYLIST_IMG_URL)
                    cap = _["play_10"]
                elif y_type == "video":
                    details, track_id = await YouTube.track(clean_url)
                    
                    if is_nsfw_content(details.get("title", "")):
                        await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", details.get("title", ""))
                        return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

                    streamtype = "youtube"
                    img = details["thumb"]
                    cap = _["play_11"].format(details["title"], details["duration_min"])
                else:
                    details, track_id = await YouTube.track(url)
                    
                    if is_nsfw_content(details.get("title", "")):
                        await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", details.get("title", ""))
                        return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

                    streamtype = "youtube"
                    img = details["thumb"]
                    cap = _["play_11"].format(details["title"], details["duration_min"])
            except Exception as e:
                try:
                    try:
                        if getattr(mystic, "text", None):
                            await mystic.edit_text(MSG_STARTING)
                            pass  # no delay
                    except: pass

                    await stream(client, _, mystic, message.from_user.id, url, chat_id, message.from_user.first_name, message.chat.id, video=video, streamtype="index", forceplay=fplay, userbot=userbot)
                    if C_LOG_STATUS:
                         try:
                             await clone_bot_logs(client, message, bot_mention, clone_logger_id, streamtype="M3u8 or Index Link")
                         except: pass
                    return await play_logs(message, streamtype="M3u8 or Index Link")
                except Exception as ex:
                    if is_vc_off(ex):
                        try:
                            return await mystic.edit_text(VC_OFF_MSG)
                        except MessageIdInvalid:
                            return await message.reply_text(VC_OFF_MSG)
                    return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> ᴇʀʀᴏʀ ғᴇᴛᴄʜɪɴɢ ᴛʀᴀᴄᴋ.")

    else:
        if len(message.command) < 2:
            try:
                C_BOT_SUPPORT_CHAT = await get_cloned_support_chat(cuser.id)
                if C_BOT_SUPPORT_CHAT:
                    C_SUPPORT_CHAT = C_BOT_SUPPORT_CHAT if "https://" in C_BOT_SUPPORT_CHAT else f"https://t.me/{C_BOT_SUPPORT_CHAT}"
                else:
                    C_SUPPORT_CHAT = config.SUPPORT_CHAT
            except:
                C_SUPPORT_CHAT = config.SUPPORT_CHAT
            buttons = InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="💬 Support", url=C_SUPPORT_CHAT), InlineKeyboardButton(text="❌ Close", callback_data="close")]]
            )
            play_img = get_random_img(config.PLAYLIST_IMG_URL) if hasattr(config, "PLAYLIST_IMG_URL") else "https://telegra.ph/file/2e3d368e77c449c287430.jpg"
            try:
                if stype == "photo" and scontent:
                     play_img = scontent
            except:
                pass
            await mystic.delete()
            return await message.reply_photo(photo=play_img, caption=_["play_18"], reply_markup=buttons, has_spoiler=True)
        
        slider = True
        query = message.text.split(None, 1)[1]
        if "-v" in query:
            query = query.replace("-v", "")
            
        clean_url, ext_id, y_type = clean_youtube_url(query)
        if y_type == "video":
            query = clean_url

        if is_nsfw_content(query):
            await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", query)
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")
        
        try:
            details, track_id = await YouTube.track(query)
            
            if is_nsfw_content(details.get("title", "")):
                await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", details.get("title", ""))
                return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

            streamtype = "youtube"
        except:
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> ᴇʀʀᴏʀ sᴇᴀʀᴄʜɪɴɢ ᴏɴ ʏᴏᴜᴛᴜʙᴇ.")

    if str(playmode) == "Direct":
        if not plist_type:
            if details["duration_min"]:
                duration_sec = time_to_seconds(details["duration_min"])
                if duration_sec > config.DURATION_LIMIT:
                    return await mystic.edit_text(_["play_6"].format(config.DURATION_LIMIT_MIN, cuser.mention))
            else:
                buttons = livestream_markup(_, track_id, user_id, "v" if video else "a", "c" if channel else "g", "f" if fplay else "d")
                return await mystic.edit_text(_["play_13"], reply_markup=InlineKeyboardMarkup(buttons))
        
        try:
            if getattr(mystic, "text", None):
                await mystic.edit_text(MSG_STARTING)
                pass  # no delay
        except: pass

        try:
            await stream(client, _, mystic, user_id, details, chat_id, user_name, message.chat.id, video=video, streamtype=streamtype, spotify=spotify, forceplay=fplay, userbot=userbot)
        except Exception as e:
            if is_vc_off(e):
                try:
                    return await mystic.edit_text(VC_OFF_MSG)
                except MessageIdInvalid:
                    return await message.reply_text(VC_OFF_MSG)
            ex_type = type(e).__name__
            err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
            print(e)
            try:
                return await mystic.edit_text(str(err))
            except MessageIdInvalid:
                return await message.reply_text(str(err))
            except MessageNotModified:
                return
        await mystic.delete()
        if C_LOG_STATUS:
            try:
                await clone_bot_logs(client, message, bot_mention, clone_logger_id, streamtype=streamtype)
            except: pass
        return await play_logs(message, streamtype=streamtype)
    else:
        if plist_type:
            ran_hash = uuid.uuid4().hex[:10].upper()
            lyrical[ran_hash] = plist_id
            buttons = playlist_markup(_, ran_hash, message.from_user.id, plist_type, "c" if channel else "g", "f" if fplay else "d")
            
            try:
                if getattr(mystic, "text", None):
                    await mystic.edit_text(MSG_STARTING)
                    pass  # no delay
            except: pass
            
            await mystic.delete()
            await message.reply_photo(photo=img, caption=cap, reply_markup=InlineKeyboardMarkup(buttons), has_spoiler=True)
            if C_LOG_STATUS:
                try:
                    await clone_bot_logs(client, message, bot_mention, clone_logger_id, streamtype=f"Playlist : {plist_type}")
                except: pass
            return await play_logs(message, streamtype=f"Playlist : {plist_type}")
        else:
            if slider:
                buttons = slider_markup(_, track_id, message.from_user.id, query, 0, "c" if channel else "g", "f" if fplay else "d")
                
                try:
                    if getattr(mystic, "text", None):
                        await mystic.edit_text(MSG_STARTING)
                        pass  # no delay
                except: pass
                
                await mystic.delete()
                await message.reply_photo(photo=details["thumb"], caption=_["play_10"].format(details["title"].title(), details["duration_min"]), reply_markup=InlineKeyboardMarkup(buttons), has_spoiler=True)
                if C_LOG_STATUS:
                    try:
                        await clone_bot_logs(client, message, bot_mention, clone_logger_id, streamtype=f"Searched on Youtube")
                    except: pass
                return await play_logs(message, streamtype=f"Searched on Youtube")
            else:
                buttons = track_markup(_, track_id, message.from_user.id, "c" if channel else "g", "f" if fplay else "d")
                
                try:
                    if getattr(mystic, "text", None):
                        await mystic.edit_text(MSG_STARTING)
                        pass  # no delay
                except: pass
                
                await mystic.delete()
                await message.reply_photo(photo=img, caption=cap, reply_markup=InlineKeyboardMarkup(buttons), has_spoiler=True)
                if C_LOG_STATUS:
                    try:
                        await clone_bot_logs(client, message, bot_mention, clone_logger_id, streamtype=f"URL Searched Inline")
                    except: pass
                return await play_logs(message, streamtype=f"URL Searched Inline")

@Client.on_callback_query(filters.regex("MusicStream") & ~BANNED_USERS)
@languageCB
async def play_music(client: Client, CallbackQuery, _):
    cuser = await client.get_me()
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    vidid, user_id, mode, cplay, fplay = callback_request.split("|")
    
    userbot = None
    use_global = False
    
    if hasattr(client, "assistant") and client.assistant:
        try:
             if not client.assistant.is_connected:
                 await client.assistant.start()
             await client.assistant.get_me()
             userbot = client.assistant
        except:
             try:
                await clonebotdb.update_one(
                    {"bot_id": client.me.id},
                    {"$unset": {"session": 1}}
                )
             except:
                pass
             
             try:
                 chat_id, _ = await get_channeplayCB(_, cplay, CallbackQuery)
                 db[chat_id] = []
                 await remove_active_chat(chat_id)
                 await remove_active_video_chat(chat_id)
             except:
                 pass

             client.assistant = None
             use_global = True
    else:
        use_global = True
        
    if use_global:
        try:
            chat_id, _ = await get_channeplayCB(_, cplay, CallbackQuery)
            userbot = await get_assistant(chat_id)
        except:
            userbot = await get_assistant(CallbackQuery.message.chat.id)
            
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return
    try:
        chat_id, channel = await get_channeplayCB(_, cplay, CallbackQuery)
    except:
        return
    user_name = CallbackQuery.from_user.mention
    try:
        await CallbackQuery.message.delete()
        await CallbackQuery.answer()
    except:
        pass
    
    mystic = await CallbackQuery.message.reply_text(MSG_DOWNLOADING)
    
    try:
        details, track_id = await YouTube.track(vidid, True)
    except:
        return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> ᴇʀʀᴏʀ ᴘʀᴏᴄᴇssɪɴɢ ʀᴇǫᴜᴇsᴛ.")

    if is_nsfw_content(details.get("title", "")):
        return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

    if details["duration_min"]:
        duration_sec = time_to_seconds(details["duration_min"])
        if duration_sec > config.DURATION_LIMIT:
            return await mystic.edit_text(_["play_6"].format(config.DURATION_LIMIT_MIN, cuser.mention))
    else:
        buttons = livestream_markup(_, track_id, CallbackQuery.from_user.id, mode, "c" if cplay == "c" else "g", "f" if fplay else "d")
        return await mystic.edit_text(_["play_13"], reply_markup=InlineKeyboardMarkup(buttons))
    video = True if mode == "v" else None
    ffplay = True if fplay == "f" else None
    
    try:
        await mystic.edit_text(MSG_STARTING)
        pass  # no delay
    except: pass

    try:
        await stream(client, _, mystic, CallbackQuery.from_user.id, details, chat_id, user_name, CallbackQuery.message.chat.id, video, streamtype="youtube", forceplay=ffplay, userbot=userbot)
    except Exception as e:
        if is_vc_off(e):
            try:
                return await mystic.edit_text(VC_OFF_MSG)
            except MessageIdInvalid:
                return await CallbackQuery.message.reply_text(VC_OFF_MSG)
        print(e)
        try:
            return await mystic.edit_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **sᴛʀᴇᴀᴍ ᴇʀʀᴏʀ:** `{str(e)}`")
        except MessageIdInvalid:
            return await CallbackQuery.message.reply_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **sᴛʀᴇᴀᴍ ᴇʀʀᴏʀ:** `{str(e)}`")
        except MessageNotModified:
            return
    return await mystic.delete()

@Client.on_callback_query(filters.regex("ZEOmousAdmin") & ~BANNED_USERS)
async def ZEOmous_check(client: Client, CallbackQuery):
    try:
        await CallbackQuery.answer("ʀᴇᴠᴇʀᴛ ʙᴀᴄᴋ ᴛᴏ ᴜsᴇʀ ᴀᴄᴄᴏᴜɴᴛ:\n\nᴏᴘᴇɴ ɢʀᴏᴜᴘ sᴇᴛᴛɪɴɢs.\n-> ᴀᴅᴍɪɴɪsᴛʀᴀᴛᴏʀs\n-> ᴄʟɪᴄᴋ ᴏɴ ʏᴏᴜʀ ɴᴀᴍᴇ\n-> ᴜɴᴄʜᴇᴄᴋ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ ᴘᴇʀᴍɪssɪᴏɴs.", show_alert=True)
    except:
        pass

@Client.on_callback_query(filters.regex("ZEOPlaylists") & ~BANNED_USERS)
@languageCB
async def play_playlists_command(client: Client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    (videoid, user_id, ptype, mode, cplay, fplay) = callback_request.split("|")
    
    userbot = None
    use_global = False
    
    if hasattr(client, "assistant") and client.assistant:
        try:
             if not client.assistant.is_connected:
                 await client.assistant.start()
             await client.assistant.get_me()
             userbot = client.assistant
        except:
             try:
                await clonebotdb.update_one(
                    {"bot_id": client.me.id},
                    {"$unset": {"session": 1}}
                )
             except:
                pass

             try:
                 chat_id, _ = await get_channeplayCB(_, cplay, CallbackQuery)
                 db[chat_id] = []
                 await remove_active_chat(chat_id)
                 await remove_active_video_chat(chat_id)
             except:
                 pass
             
             client.assistant = None
             use_global = True
    else:
        use_global = True
        
    if use_global:
        try:
            chat_id, _ = await get_channeplayCB(_, cplay, CallbackQuery)
            userbot = await get_assistant(chat_id)
        except:
            userbot = await get_assistant(CallbackQuery.message.chat.id)

    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return
    try:
        chat_id, channel = await get_channeplayCB(_, cplay, CallbackQuery)
    except:
        return
    user_name = CallbackQuery.from_user.mention
    await CallbackQuery.message.delete()
    try:
        await CallbackQuery.answer()
    except:
        pass
    
    mystic = await CallbackQuery.message.reply_text(MSG_DOWNLOADING)

    videoid = lyrical.get(videoid)
    video = True if mode == "v" else None
    ffplay = True if fplay == "f" else None
    spotify = True
    if ptype == "yt":
        spotify = False
        try:
            result = await YouTube.playlist(videoid, config.PLAYLIST_FETCH_LIMIT, CallbackQuery.from_user.id, True)
        except:
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> ᴇʀʀᴏʀ ғᴇᴛᴄʜɪɴɢ ᴘʟᴀʏʟɪsᴛ.")
    if ptype == "spplay":
        try:
            result, spotify_id = await Spotify.playlist(videoid)
        except:
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> ᴇʀʀᴏʀ ғᴇᴛᴄʜɪɴɢ sᴘᴏᴛɪғʏ ᴘʟᴀʏʟɪsᴛ.")
    if ptype == "spalbum":
        try:
            result, spotify_id = await Spotify.album(videoid)
        except:
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> ᴇʀʀᴏʀ ғᴇᴛᴄʜɪɴɢ sᴘᴏᴛɪғʏ ᴀʟʙᴜᴍ.")
    if ptype == "spartist":
        try:
            result, spotify_id = await Spotify.artist(videoid)
        except:
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> ᴇʀʀᴏʀ ғᴇᴛᴄʜɪɴɢ sᴘᴏᴛɪғʏ ᴀʀᴛɪsᴛ.")
    if ptype == "apple":
        try:
            result, apple_id = await Apple.playlist(videoid, True)
        except:
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> ᴇʀʀᴏʀ ғᴇᴛᴄʜɪɴɢ ᴀᴘᴘʟᴇ ᴘʟᴀʏʟɪsᴛ.")
            
    try:
        await mystic.edit_text(MSG_STARTING)
        pass  # no delay
    except: pass

    try:
        await stream(client, _, mystic, user_id, result, chat_id, user_name, CallbackQuery.message.chat.id, video, streamtype="playlist", spotify=spotify, forceplay=ffplay, userbot=userbot)
    except Exception as e:
        if is_vc_off(e):
            try:
                return await mystic.edit_text(VC_OFF_MSG)
            except MessageIdInvalid:
                return await CallbackQuery.message.reply_text(VC_OFF_MSG)
        print(e)
        try:
            return await mystic.edit_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **sᴛʀᴇᴀᴍ ᴇʀʀᴏʀ:** `{str(e)}`")
        except MessageIdInvalid:
            return await CallbackQuery.message.reply_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **sᴛʀᴇᴀᴍ ᴇʀʀᴏʀ:** `{str(e)}`")
        except MessageNotModified:
            return
    return await mystic.delete()

@Client.on_callback_query(filters.regex("slider") & ~BANNED_USERS)
@languageCB
async def slider_queries(client: Client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    (what, rtype, query, user_id, cplay, fplay) = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return
    what = str(what)
    rtype = int(rtype)
    if what == "F":
        if rtype == 9:
            query_type = 0
        else:
            query_type = int(rtype + 1)
        try:
            await CallbackQuery.answer(_["playcb_2"])
        except:
            pass
        title, duration_min, thumbnail, vidid = await YouTube.slider(query, query_type)

        if is_nsfw_content(title):
            try: await CallbackQuery.message.delete()
            except: pass
            return await app.send_message(CallbackQuery.message.chat.id, "<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

        buttons = slider_markup(_, vidid, user_id, query, query_type, cplay, fplay)
        med = InputMediaPhoto(media=thumbnail, caption=_["play_10"].format(title.title(), duration_min), has_spoiler=True)
        try:
            await CallbackQuery.edit_message_media(media=med, reply_markup=InlineKeyboardMarkup(buttons))
        except:
            pass
    if what == "B":
        if rtype == 0:
            query_type = 9
        else:
            query_type = int(rtype - 1)
        try:
            await CallbackQuery.answer(_["playcb_2"])
        except:
            pass
        title, duration_min, thumbnail, vidid = await YouTube.slider(query, query_type)
        
        if is_nsfw_content(title):
            try: await CallbackQuery.message.delete()
            except: pass
            return await app.send_message(CallbackQuery.message.chat.id, "<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

        buttons = slider_markup(_, vidid, user_id, query, query_type, cplay, fplay)
        med = InputMediaPhoto(media=thumbnail, caption=_["play_10"].format(title.title(), duration_min), has_spoiler=True)
        try:
            await CallbackQuery.edit_message_media(media=med, reply_markup=InlineKeyboardMarkup(buttons))
        except:
            pass

async def stream(client, _, mystic, user_id, result, chat_id, user_name, original_chat_id, video: Union[bool, str] = None, streamtype: Union[bool, str] = None, spotify: Union[bool, str] = None, forceplay: Union[bool, str] = None, userbot=None):
    try:
        a = await client.get_me()
        bot_username = a.username
        if hasattr(client, "support_chat") and client.support_chat:
            C_SUPPORT_CHAT = client.support_chat
        else:
            C_BOT_SUPPORT_CHAT = await get_cloned_support_chat(a.id)
            if C_BOT_SUPPORT_CHAT:
                C_SUPPORT_CHAT = C_BOT_SUPPORT_CHAT if "https://" in C_BOT_SUPPORT_CHAT else f"https://t.me/{C_BOT_SUPPORT_CHAT}"
                client.support_chat = C_SUPPORT_CHAT
            else:
                C_SUPPORT_CHAT = config.SUPPORT_CHAT
    except:
        C_SUPPORT_CHAT = config.SUPPORT_CHAT
        bot_username = client.me.username
        
    if not result:
        return
    if forceplay:
        await ANJALI.force_stop_stream(chat_id)
    
    bot_id = client.me.id
    custom_caption = await get_clone_stream_caption(bot_id)

    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0
        for search in result:
            if int(count) == config.PLAYLIST_FETCH_LIMIT:
                continue
            try:
                (title, duration_min, duration_sec, thumbnail, vidid) = await YouTube.details(search, False if spotify else True)
            except:
                continue
            if str(duration_min) == "None":
                continue
            if duration_sec > config.DURATION_LIMIT:
                continue
            if await is_active_chat(chat_id):
                await put_queue(chat_id, original_chat_id, f"vid_{vidid}", title, duration_min, user_name, vidid, user_id, "video" if video else "audio")
                db[chat_id][-1]["client"] = client
                position = len(db.get(chat_id)) - 1
                count += 1
                msg += f"{count}. {title[:70]}\n"
                msg += f"{_['play_20']} {position}\n\n"
            else:
                if not forceplay:
                    db[chat_id] = []
                status = True if video else None
                try:
                    file_path, direct = await YouTube.download(vidid, mystic, video=status, videoid=True)
                except:
                    continue
                
                if not file_path or str(file_path) == "None":
                    continue
                
                await ANJALI.join_call(chat_id, original_chat_id, file_path, video=status, image=thumbnail, userbot=userbot)
                
                await put_queue(chat_id, original_chat_id, file_path if direct else f"vid_{vidid}", title, duration_min, user_name, vidid, user_id, "video" if video else "audio", forceplay=forceplay)
                db[chat_id][-1]["client"] = client
                img = await get_thumb(vidid, user_id, client)
                
                button = panel_markup_clone(_, vidid, chat_id)
                
                link = f"https://t.me/{bot_username}?start=info_{vidid}"
                if custom_caption:
                    try:
                        final_caption = custom_caption.format(link, title[:25], duration_min, user_name)
                    except:
                        final_caption = _["stream_1"].format(link, title[:25], duration_min, user_name)
                else:
                    final_caption = _["stream_1"].format(link, title[:25], duration_min, user_name)

                run = await client.send_photo(original_chat_id, photo=img, caption=final_caption, reply_markup=InlineKeyboardMarkup(button), has_spoiler=True)
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
        if count == 0:
            return
        else:
            link = await ANJALIBin(msg)
            upl = close_markup(_)
            return await client.send_message(original_chat_id, text=_["play_21"].format(position, link), reply_markup=upl)

    elif streamtype == "youtube":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        duration_min = result["duration_min"]
        thumbnail = result["thumb"]
        status = True if video else None
        try:
            file_path, direct = await YouTube.download(vidid, mystic, videoid=True, video=status)
        except:
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> ᴇʀʀᴏʀ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴠɪᴅᴇᴏ.")
        
        if not file_path or str(file_path) == "None":
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Error:** Download failed (yt-dlp could not extract media).")

        if await is_active_chat(chat_id):
            await put_queue(chat_id, original_chat_id, file_path if direct else f"vid_{vidid}", title, duration_min, user_name, vidid, user_id, "video" if video else "audio")
            db[chat_id][-1]["client"] = client
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await client.send_message(chat_id=original_chat_id, text=_["queue_4"].format(position, title[:18], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
        else:
            if not forceplay:
                db[chat_id] = []
                
            await ANJALI.join_call(chat_id, original_chat_id, file_path, video=status, image=thumbnail, userbot=userbot)
            
            await put_queue(chat_id, original_chat_id, file_path if direct else f"vid_{vidid}", title, duration_min, user_name, vidid, user_id, "video" if video else "audio", forceplay=forceplay)
            db[chat_id][-1]["client"] = client
            img = await get_thumb(vidid, user_id, client)
            
            button = panel_markup_clone(_, vidid, chat_id)
            
            link = f"https://t.me/{bot_username}?start=info_{vidid}"
            if custom_caption:
                try:
                    final_caption = custom_caption.format(link, title[:25], duration_min, user_name)
                except:
                    final_caption = _["stream_1"].format(link, title[:25], duration_min, user_name)
            else:
                final_caption = _["stream_1"].format(link, title[:25], duration_min, user_name)

            run = await client.send_photo(original_chat_id, photo=img, caption=final_caption, reply_markup=InlineKeyboardMarkup(button), has_spoiler=True)
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
            
    elif streamtype == "soundcloud":
        file_path = result["filepath"]
        title = result["title"]
        duration_min = result["duration_min"]
        if await is_active_chat(chat_id):
            await put_queue(chat_id, original_chat_id, file_path, title, duration_min, user_name, streamtype, user_id, "audio")
            db[chat_id][-1]["client"] = client
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await client.send_message(chat_id=original_chat_id, text=_["queue_4"].format(position, title[:18], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
        else:
            if not forceplay:
                db[chat_id] = []
            await ANJALI.join_call(chat_id, original_chat_id, file_path, video=None, userbot=userbot)
            await put_queue(chat_id, original_chat_id, file_path, title, duration_min, user_name, streamtype, user_id, "audio", forceplay=forceplay)
            db[chat_id][-1]["client"] = client
            
            button = stream_markup2(_, chat_id)
            sc_img = config.SOUNCLOUD_IMG_URL
            run = await client.send_photo(original_chat_id, photo=sc_img, caption=_["stream_1"].format(C_SUPPORT_CHAT, title[:23], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button), has_spoiler=True)
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    elif streamtype == "telegram":
        file_path = result["path"]
        link = result["link"]
        title = (result["title"]).title()
        duration_min = result["dur"]
        status = True if video else None
        if await is_active_chat(chat_id):
            await put_queue(chat_id, original_chat_id, file_path, title, duration_min, user_name, streamtype, user_id, "video" if video else "audio")
            db[chat_id][-1]["client"] = client
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await client.send_message(chat_id=original_chat_id, text=_["queue_4"].format(position, title[:18], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
        else:
            if not forceplay:
                db[chat_id] = []
            await ANJALI.join_call(chat_id, original_chat_id, file_path, video=status, userbot=userbot)
            await put_queue(chat_id, original_chat_id, file_path, title, duration_min, user_name, streamtype, user_id, "video" if video else "audio", forceplay=forceplay)
            db[chat_id][-1]["client"] = client
            if video: await add_active_video_chat(chat_id)
            
            button = stream_markup2(_, chat_id)
            tg_img = config.TELEGRAM_VIDEO_URL if video else config.TELEGRAM_AUDIO_URL
            run = await client.send_photo(original_chat_id, photo=tg_img, caption=_["stream_1"].format(link, title[:23], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button), has_spoiler=True)
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    elif streamtype == "live":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        thumbnail = result["thumb"]
        duration_min = "Live Track"
        status = True if video else None
        if await is_active_chat(chat_id):
            await put_queue(chat_id, original_chat_id, f"live_{vidid}", title, duration_min, user_name, vidid, user_id, "video" if video else "audio")
            db[chat_id][-1]["client"] = client
            position = len(db.get(chat_id)) - 1
            button = aq_markup(_, chat_id)
            await client.send_message(chat_id=original_chat_id, text=_["queue_4"].format(position, title[:18], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button))
        else:
            if not forceplay:
                db[chat_id] = []
            n, file_path = await YouTube.video(link)
            
            if n == 0 or not file_path or str(file_path) == "None":
                raise AssistantErr(_["str_3"])
            
            await ANJALI.join_call(chat_id, original_chat_id, file_path, video=status, image=thumbnail if thumbnail else None, userbot=userbot)
            await put_queue(chat_id, original_chat_id, f"live_{vidid}", title, duration_min, user_name, vidid, user_id, "video" if video else "audio", forceplay=forceplay)
            db[chat_id][-1]["client"] = client
            img = await get_thumb(vidid, user_id, client)
            
            button = stream_markup2(_, chat_id)
            run = await client.send_photo(original_chat_id, photo=img, caption=_["stream_1"].format(f"https://t.me/{bot_username}?start=info_{vidid}", title[:23], duration_min, user_name), reply_markup=InlineKeyboardMarkup(button), has_spoiler=True)
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    elif streamtype == "index":
        link = result
        title = "Index or M3u8 Link"
        duration_min = "00:00"
        if await is_active_chat(chat_id):
            await put_queue_index(chat_id, original_chat_id, "index_url", title, duration_min, user_name, link, "video" if video else "audio")
            db[chat_id][-1]["client"] = client
            await mystic.edit_text("<tg-emoji emoji-id=\"6280269890821558384\">✅</tg-emoji> **Added to Queue.**")
        else:
            if not forceplay:
                db[chat_id] = []
            await ANJALI.join_call(chat_id, original_chat_id, link, video=True if video else None, userbot=userbot)
            await put_queue_index(chat_id, original_chat_id, "index_url", title, duration_min, user_name, link, "video" if video else "audio", forceplay=forceplay)
            db[chat_id][-1]["client"] = client
            
            button = stream_markup2(_, chat_id)
            stream_img = config.STREAM_IMG_URL
            run = await client.send_photo(original_chat_id, photo=stream_img, caption=_["stream_2"].format(user_name), reply_markup=InlineKeyboardMarkup(button), has_spoiler=True)
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await mystic.delete()
