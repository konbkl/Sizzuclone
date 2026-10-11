from pyrogram import Client, filters, enums
from pyrogram.enums import ParseMode, ButtonStyle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
import random

# Make sure config se LOGGER_2_ID import ho raha hai
from SHIVMUSIC import app
from SHIVMUSIC.utils.database import is_on_off
from config import LOGGER_ID, LOGGER_2_ID

# 🔥 PREMIUM EMOJIS LIST 🔥
PREMIUM_EMOJIS = [
    "5422831825178206894", 
    "5368324170673489600",
    "5206607081334906820",
    "5206380668048496464"
]

# ====================================================
# HELPER FUNCTION: To Fetch Group Owner
# ====================================================
async def get_owner(client, chat_id):
    try:
        async for member in client.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            if member.status == enums.ChatMemberStatus.OWNER:
                return member.user.mention
    except:
        pass
    return "Unknown"


# ====================================================
# PLAY LOGS
# ====================================================
async def play_logs(message, streamtype):
    if await is_on_off(2):
        try:
            query = message.text.split(None, 1)[1]
        except:
            query = "Link/File or Reply"

        try:
            members_count = await app.get_chat_members_count(message.chat.id)
        except:
            members_count = "Unknown"
            
        owner = await get_owner(app, message.chat.id)

        chat_link = None
        if message.chat.username:
            chat_link = f"https://t.me/{message.chat.username}"
        else:
            try:
                chat_link = await app.export_chat_invite_link(message.chat.id)
            except:
                pass

        logger_text = f"""
<blockquote><b>{app.mention} ᴘʟᴀʏ ʟᴏɢ</b>

<b>• ʀᴇǫᴜᴇsᴛ ʙʏ : {message.from_user.mention}</b>
<b>• ǫᴜᴇʀʏ : {query}</b>
<b>• ᴄʜᴀᴛ : {message.chat.title} [<code>{message.chat.id}</code>]</b>
<b>• ᴏᴡɴᴇʀ : {owner}</b>
<b>• ᴍᴇᴍʙᴇʀs : {members_count}</b></blockquote>
"""
        buttons = []
        if chat_link:
            buttons.append([InlineKeyboardButton("ɢʀᴏᴜᴘ ʟɪɴᴋ", url=chat_link, style=ButtonStyle.PRIMARY, icon_custom_emoji_id=random.choice(PREMIUM_EMOJIS))])
        buttons.append([InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/betabot_support")])
        
        reply_markup = InlineKeyboardMarkup(buttons)

        if message.chat.id != LOGGER_ID:
            try:
                await app.send_message(
                    chat_id=LOGGER_ID,
                    text=logger_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=reply_markup
                )
            except:
                pass
        return


# ====================================================
# CLONE BOT PLAY LOGS
# ====================================================
async def clone_bot_logs(client, message, bot_mention, clone_logger_id, streamtype):
    bot = await client.get_me()
    try:
        query = message.text.split(None, 1)[1]
    except:
        query = "Link/File or Reply"

    if clone_logger_id:
        owner_log_text = f"""
<b><a href="https://t.me/{bot.username}">{bot.first_name}</a> ᴘʟᴀʏ ʟᴏɢ</b>

<b>• ʀᴇǫᴜᴇsᴛ ʙʏ :</b> {message.from_user.mention}
<b>• ǫᴜᴇʀʏ :</b> {query}
<b>• ᴄʜᴀᴛ :</b> {message.chat.title} [<code>{message.chat.id}</code>]
"""     
        owner_reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/betabot_support")]]
        )

        if message.chat.id != int(clone_logger_id):
            try:
                await client.send_message(
                    chat_id=int(clone_logger_id),
                    text=owner_log_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=owner_reply_markup
                )
            except Exception as e:
                print(f"[ERROR] Sending to Clone Owner Log Failed: {e}")

    if LOGGER_ID:
        try:
            members_count = await client.get_chat_members_count(message.chat.id)
        except:
            members_count = "Unknown"
            
        owner = await get_owner(client, message.chat.id)

        chat_link = None
        if message.chat.username:
            chat_link = f"https://t.me/{message.chat.username}"
        else:
            try:
                chat_link = await client.export_chat_invite_link(message.chat.id)
            except:
                pass

        admin_log_text = f"""
<blockquote><b>🤖 ᴄʟᴏɴᴇ ʙᴏᴛ ʟᴏɢ : @{bot.username}</b>

<b>• ʀᴇǫᴜᴇsᴛ ʙʏ : {message.from_user.mention}</b>
<b>• ǫᴜᴇʀʏ : {query}</b>
<b>• ᴄʜᴀᴛ : {message.chat.title} [<code>{message.chat.id}</code>]</b>
<b>• ᴏᴡɴᴇʀ : {owner}</b>
<b>• ᴍᴇᴍʙᴇʀs : {members_count}</b></blockquote>
"""
        buttons = []
        if chat_link:
            buttons.append([InlineKeyboardButton("ɢʀᴏᴜᴘ ʟɪɴᴋ", url=chat_link, style=ButtonStyle.PRIMARY, icon_custom_emoji_id=random.choice(PREMIUM_EMOJIS))])
        buttons.append([InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/betabot_support")])
        
        reply_markup = InlineKeyboardMarkup(buttons)

        try:
            await app.send_message(
                chat_id=LOGGER_ID,
                text=admin_log_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"[ERROR] Sending to Main Admin Log Failed: {e}")


# ====================================================
# AUTO GROUP ADD/REMOVE EVENT LOGGER
# ====================================================
@app.on_chat_member_updated(filters.group, group=1)
async def auto_group_logger(client: Client, message: ChatMemberUpdated):
    try:
        bot = await client.get_me()
        
        # Sirf tabhi trigger hoga jab bot khud add/remove ho
        if not message.new_chat_member or message.new_chat_member.user.id != bot.id:
            return

        # Main Bot vs Clone Bot Check
        is_clone = False if bot.id == app.id else True
        target_logger = LOGGER_2_ID if is_clone else LOGGER_ID
        
        if not target_logger:
            return

        chat = message.chat
        action_by = message.from_user
        
        try:
            members_count = await client.get_chat_members_count(chat.id)
        except:
            members_count = "Unknown"

        owner = await get_owner(client, chat.id)
        action_by_mention = action_by.mention if action_by else "<b>Unknown User</b>"
        bot_details = f"@{bot.username} (Clone)" if is_clone else app.mention
        
        # Image URL
        log_image = "https://files.catbox.moe/10zwqs.jpg"

        # Group Link Fetching Logic for Button
        chat_link = None
        if chat.username:
            chat_link = f"https://t.me/{chat.username}"
        elif message.new_chat_member.status == enums.ChatMemberStatus.ADMINISTRATOR:
            try:
                chat_link = await client.export_chat_invite_link(chat.id)
            except:
                pass

        # Button Setup
        reply_markup = None
        if chat_link:
            buttons = [
                [InlineKeyboardButton("🔗 ɢʀᴏᴜᴘ ʟɪɴᴋ", url=chat_link)]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)

        # 🟢 CONDITION 1: Added to Group
        if message.new_chat_member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR]:
            log_caption = f"""
#Added
<blockquote><b>✅ ʙᴏᴛ ᴀᴅᴅᴇᴅ ᴛᴏ ɢʀᴏᴜᴘ</b>

<b>• ʙᴏᴛ : {bot_details}</b>
<b>• ᴀᴅᴅᴇᴅ ʙʏ : {action_by_mention}</b>
<b>• ᴄʜᴀᴛ : {chat.title} [<code>{chat.id}</code>]</b>
<b>• ᴏᴡɴᴇʀ : {owner}</b>
<b>• ᴍᴇᴍʙᴇʀs : {members_count}</b></blockquote>
"""
            await client.send_photo(
                chat_id=target_logger,
                photo=log_image,
                caption=log_caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )

        # 🔴 CONDITION 2: Removed from Group
        elif message.new_chat_member.status in [enums.ChatMemberStatus.BANNED, enums.ChatMemberStatus.LEFT]:
            log_caption = f"""
#Removed
<blockquote><b>❌ ʙᴏᴛ ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ɢʀᴏᴜᴘ</b>

<b>• ʙᴏᴛ : {bot_details}</b>
<b>• ʀᴇᴍᴏᴠᴇᴅ ʙʏ : {action_by_mention}</b>
<b>• ᴄʜᴀᴛ : {chat.title} [<code>{chat.id}</code>]</b>
<b>• ᴏᴡɴᴇʀ : {owner}</b>
<b>• ᴍᴇᴍʙᴇʀs : {members_count}</b></blockquote>
"""
            await client.send_photo(
                chat_id=target_logger,
                photo=log_image,
                caption=log_caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )

    except Exception as e:
        print(f"[ERROR] Auto Group Logger Failed: {e}")


# ====================================================
# AUTOPLAY LOGS 
# ====================================================
async def autoplay_log(client, chat_id, query, vibe="Unknown", is_clone=False, clone_logger_id=None):
    if not await is_on_off(2):
        return
        
    try:
        bot = await client.get_me()
        bot_mention = bot.mention
    except:
        return

    try:
        chat = await client.get_chat(chat_id)
        chat_title = chat.title
        chat_username = chat.username
    except:
        chat_title = "Unknown Chat"
        chat_username = None

    try:
        members_count = await client.get_chat_members_count(chat_id)
    except:
        members_count = "Unknown"
        
    owner = await get_owner(client, chat_id)

    chat_link = None
    if chat_username:
        chat_link = f"https://t.me/{chat_username}"
    else:
        try:
            chat_link = await client.export_chat_invite_link(chat_id)
        except:
            pass

    if is_clone and clone_logger_id:
        owner_autoplay_text = f"""
<b><a href="https://t.me/{bot.username}">{bot.first_name}</a> ᴀᴜᴛᴏᴘʟᴀʏ ʟᴏɢ</b>

<b>• ᴀᴄᴛɪᴏɴ : ᴀᴜᴛᴏᴘʟᴀʏ ᴛʀɪɢɢᴇʀᴇᴅ 🔄</b>
<b>• ᴛʀᴀᴄᴋ :</b> {query}
<b>• ᴠɪʙᴇ :</b> {vibe}
<b>• ᴄʜᴀᴛ :</b> {chat_title} [<code>{chat_id}</code>]
"""
        owner_reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/betabot_support")]]
        )

        if chat_id != int(clone_logger_id):
            try:
                await client.send_message(
                    chat_id=int(clone_logger_id),
                    text=owner_autoplay_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=owner_reply_markup
                )
            except Exception as e:
                print(f"[ERROR] Sending to Clone Owner Autoplay Log Failed: {e}")

    if is_clone:
        header_text = f"🤖 <b>ᴄʟᴏɴᴇ ᴀᴜᴛᴏᴘʟᴀʏ ʟᴏɢ : @{bot.username}</b>"
    else:
        header_text = f"<b>{bot_mention} ᴀᴜᴛᴏᴘʟᴀʏ ʟᴏɢ</b>"

    logger_text = f"""
<blockquote>{header_text}

<b>• ᴀᴄᴛɪᴏɴ : ᴀᴜᴛᴏᴘʟᴀʏ ᴛʀɪɢɢᴇʀᴇᴅ 🔄</b>
<b>• ᴛʀᴀᴄᴋ : {query}</b>
<b>• ᴠɪʙᴇ : {vibe}</b>
<b>• ᴄʜᴀᴛ : {chat_title} [<code>{chat_id}</code>]</b>
<b>• ᴏᴡɴᴇʀ : {owner}</b>
<b>• ᴍᴇᴍʙᴇʀs : {members_count}</b></blockquote>
"""
    buttons = []
    if chat_link:
        buttons.append([InlineKeyboardButton("ɢʀᴏᴜᴘ ʟɪɴᴋ", url=chat_link, style=ButtonStyle.SUCCESS, icon_custom_emoji_id=random.choice(PREMIUM_EMOJIS))])
    buttons.append([InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/betabot_support")])
    
    reply_markup = InlineKeyboardMarkup(buttons)

    if chat_id != LOGGER_ID:
        try:
            await app.send_message(
                chat_id=LOGGER_ID,
                text=logger_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"[ERROR] Sending Autoplay Log Failed: {e}")


# ====================================================
# AUTOPLAY LOGS (main bot + clone bots)
# ====================================================
async def autoplay_logs(client, chat_id, title, vidid=None, is_clone=False):
    """Log every autoplay track.

    Main bot  -> LOGGER_ID.
    Clone bot -> clone owner's log channel (or owner DM) + main LOGGER_ID.
    """
    try:
        try:
            chat = await client.get_chat(chat_id)
            chat_title = chat.title or "Private"
        except Exception:
            chat_title = "Unknown"

        try:
            me = client.me or await client.get_me()
            bot_name, bot_user = me.first_name, me.username
        except Exception:
            bot_name, bot_user = "Bot", None

        link = f"https://youtu.be/{vidid}" if vidid and len(str(vidid)) == 11 else None
        song = f'<a href="{link}">{title}</a>' if link else title
        head = f"🤖 ᴄʟᴏɴᴇ ᴀᴜᴛᴏᴘʟᴀʏ ʟᴏɢ : @{bot_user}" if is_clone else f"{bot_name} ᴀᴜᴛᴏᴘʟᴀʏ ʟᴏɢ"
        text = (
            f"<blockquote><b>{head}</b>\n\n"
            f"<b>• ʀᴇǫᴜᴇsᴛ ʙʏ :</b> ᴀᴜᴛᴏᴘʟᴀʏ 🎧\n"
            f"<b>• sᴏɴɢ :</b> {song}\n"
            f"<b>• ᴄʜᴀᴛ :</b> {chat_title} [<code>{chat_id}</code>]</blockquote>"
        )

        if is_clone:
            try:
                from SHIVMUSIC.cplugin.setinfo import get_log_channel
                from SHIVMUSIC.utils.database.clonedb import get_owner_id_from_db
                target = await get_log_channel(me.id)
                if not target or str(target) == "-100":
                    target = await get_owner_id_from_db(me.id)
                if target and int(target) != int(chat_id):
                    await client.send_message(int(target), text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            except Exception as e:
                print(f"[AUTOPLAY CLONE LOG] {e}")

        if LOGGER_ID and int(chat_id) != int(LOGGER_ID):
            await app.send_message(LOGGER_ID, text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        print(f"[AUTOPLAY LOG] {e}")
