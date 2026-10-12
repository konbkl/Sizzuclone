import os
import re
import random
import aiofiles
import aiohttp
import math
from PIL import (Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps)

# Nayi library yahan update kar di gayi hai 👇
from youtubesearchpython.__future__ import VideosSearch
from SHIVMUSIC import app
from SHIVMUSIC.utils.database import clonebotdb

# --- HELPER FUNCTIONS ---
def get_glowing_circle(image):
    img = image.convert("RGBA")
    size = min(img.size)
    img = ImageOps.fit(img, (size, size), centering=(0.5, 0.5))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    
    circular_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    circular_img.paste(img, (0, 0), mask)
    
    offset = 50
    glow_size = size + (offset * 2)
    glow = Image.new("RGBA", (glow_size, glow_size), (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(glow)
    
    draw_glow.ellipse((5, 5, glow_size-5, glow_size-5), fill=(255, 255, 0, 60))
    draw_glow.ellipse((15, 15, glow_size-15, glow_size-15), fill=(255, 255, 255, 80))
    draw_glow.ellipse((25, 25, glow_size-25, glow_size-25), fill=(255, 105, 180, 150))
    draw_glow.ellipse((35, 35, glow_size-35, glow_size-35), fill=(255, 255, 255, 200))
    glow = glow.filter(ImageFilter.GaussianBlur(15))
    
    draw_border = ImageDraw.Draw(glow)
    draw_border.ellipse((offset - 4, offset - 4, size + offset + 4, size + offset + 4), outline="white", width=8)
    glow.paste(circular_img, (offset, offset), circular_img)
    return glow, offset

def clear(text, max_length=25):
    text = text.strip()
    return text[:max_length].rstrip() + "..." if len(text) > max_length else text

async def download_user_photo(user_id):
    try:
        async for photo in app.get_chat_photos(user_id, limit=1):
            return await app.download_media(photo.file_id, file_name=f"cache/{user_id}.jpg")
    except: 
        return None
    return None

# --- MAIN THUMBNAIL FUNCTION ---
async def _old_get_thumb(videoid, user_id, client):
    # Fetching Bot and Owner details
    me = await client.get_me()
    bot_name = me.first_name.upper() if me.first_name else "MUSIC BOT"
    bot_id = me.id
    owner_name = "ADMIN"
    
    try:
        bot_data = await clonebotdb.find_one({"bot_id": bot_id})
        if bot_data and bot_data.get("user_id"):
            owner = await client.get_users(bot_data.get("user_id"))
            owner_name = owner.first_name.upper() if owner.first_name else "OWNER"
    except Exception as e: 
        owner_name = "ADMIN"

    os.makedirs("cache", exist_ok=True)
    filename = f"cache/{videoid}_{bot_id}.png"
    if os.path.isfile(filename): 
        return filename

    results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
    data = await results.next()
    result = data["result"][0]
    title = re.sub(r"\W+", " ", result["title"]).title()
    duration = result.get("duration", "00:00")
    views = result.get("viewCount", {}).get("short", "Unknown")
    channel = result.get("channel", {}).get("name", "Unknown Artist")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(result["thumbnails"][0]["url"].split("?")[0]) as resp:
            f = await aiofiles.open(f"cache/temp_{videoid}.jpg", mode="wb")
            await f.write(await resp.read())
            await f.close()

    bg = Image.open(f"cache/temp_{videoid}.jpg").convert("RGBA").resize((1920, 1080))
    background = bg.filter(ImageFilter.GaussianBlur(25)).point(lambda p: p * 0.4)
    
    black_card = Image.new("RGBA", background.size, (0, 0, 0, 0))
    draw_card = ImageDraw.Draw(black_card)
    draw_card.rounded_rectangle((40, 40, 1880, 940), radius=60, fill=(0, 0, 0, 255), outline=(132, 224, 240, 200), width=6)
    background = Image.alpha_composite(background, black_card)
    draw = ImageDraw.Draw(background)

    try:
        f1 = ImageFont.truetype("SHIVMUSIC/assets/font.ttf", 65)
        f2 = ImageFont.truetype("SHIVMUSIC/assets/font2.ttf", 45)
        br = ImageFont.truetype("SHIVMUSIC/assets/font2.ttf", 50)
        f_small = ImageFont.truetype("SHIVMUSIC/assets/font2.ttf", 30)
    except:
        f1 = f2 = br = f_small = ImageFont.load_default()

    # --- BRANDING & TOP TEXT (BOT NAME & OWNER NAME) ---
    bot_text = f"BOT: {bot_name}"
    owner_text = f"OWNER: {owner_name}"
    
    # Left Aligned Bot Name
    draw.text((80, 60), bot_text, fill="#FFFF00", font=br) # Yellow color
    
    # Right Aligned Owner Name (Automatically adjusts based on text length)
    try:
        owner_w = br.getlength(owner_text)
    except AttributeError:
        # Fallback for older PIL versions
        owner_w = draw.textsize(owner_text, font=br)[0] if hasattr(draw, 'textsize') else 400
        
    draw.text((1840 - owner_w, 60), owner_text, fill="#00FFFF", font=br) # Cyan color

    # --- IMAGES ---
    yt_img_glowing, yt_offset = get_glowing_circle(bg.resize((500, 500)))
    background.paste(yt_img_glowing, (80 - yt_offset, 250 - yt_offset), yt_img_glowing)
    
    u_photo = await download_user_photo(user_id)
    if u_photo:
        # Yahan par GaussianBlur(6) apply kiya gaya hai 👇
        u_img_blurred = Image.open(u_photo).resize((450, 450)).filter(ImageFilter.GaussianBlur(6))
        u_img_glowing, u_offset = get_glowing_circle(u_img_blurred)
        background.paste(u_img_glowing, (1350 - u_offset, 250 - u_offset), u_img_glowing)

    draw.text((650, 300), clear(title, 25), fill="white", font=f1)
    draw.text((650, 400), f"Artist: {channel}", fill=(200, 200, 200), font=f2)
    draw.text((650, 470), f"Views: {views}", fill=(150, 150, 150), font=f2)
    draw.text((650, 530), f"Duration: {duration}", fill=(150, 150, 150), font=f2)

    # --- UNIFORM WAVEFORM ---
    bar_count = 64; bar_width = 4; bar_gap = 10
    total_width = bar_count * bar_gap
    start_x = (1920 - total_width) / 2; base_y = 780
    for i in range(bar_count):
        dist_from_center = abs(i - (bar_count / 2))
        h = 35 if dist_from_center < 5 else 20
        x0 = start_x + (i * bar_gap); y0 = base_y - h; x1 = x0 + bar_width; y1 = base_y + h
        fill_color = (255, 255, 255, 255) if i < (bar_count // 2) else (150, 150, 150, 200)
        draw.rounded_rectangle((x0, y0, x1, y1), radius=2, fill=fill_color)

    # --- PROCESSING LINE & ICONS ---
    line_y = base_y + 60
    draw.line([(start_x, line_y), (start_x + total_width, line_y)], fill=(100, 100, 100), width=1)
    draw.line([(start_x, line_y), (start_x + (total_width // 2), line_y)], fill=(255, 255, 255), width=2)
    thumb_x = start_x + (total_width // 2)
    draw.ellipse((thumb_x - 8, line_y - 8, thumb_x + 8, line_y + 8), fill="white")
    draw.ellipse((thumb_x - 3, line_y - 3, thumb_x + 3, line_y + 3), fill=(0, 0, 0))
    
    draw.text((start_x, line_y + 20), "00:00", fill="white", font=f_small)
    draw.text((start_x + total_width - 80, line_y + 20), duration, fill="white", font=f_small)

    ctrl_y = line_y + 50; mid_x = 960 # Higher up
    draw.ellipse((mid_x - 25, ctrl_y - 25, mid_x + 25, ctrl_y + 25), outline="white", width=2)
    draw.polygon([(mid_x - 6, ctrl_y - 10), (mid_x + 10, ctrl_y), (mid_x - 6, ctrl_y + 10)], fill="white")
    draw.ellipse((mid_x - 60, ctrl_y - 15, mid_x - 35, ctrl_y + 15), outline="white", width=1)
    draw.ellipse((mid_x + 35, ctrl_y - 15, mid_x + 60, ctrl_y + 15), outline="white", width=1)

    background.convert("RGB").save(filename)
    if os.path.exists(f"cache/temp_{videoid}.jpg"): os.remove(f"cache/temp_{videoid}.jpg")
    if u_photo and os.path.exists(u_photo): os.remove(u_photo)
    return filename


# ---- New glowing player card; the old generator stays as a fallback ----
from SHIVMUSIC.utils.playercard import make_player_card


async def get_thumb(videoid, user_id, client=None):
    path = await make_player_card(videoid, user_id)
    if path:
        return path
    return await _old_get_thumb(videoid, user_id, client)
