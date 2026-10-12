"""Now-playing player card (1280x720) with soft glowing buttons and lines.

    path = await make_player_card(videoid)

Used by both thumbnail modules (main bot + clone bots). Everything is drawn at
2x and scaled down, so edges stay smooth.
"""

import asyncio
import math
import os
from io import BytesIO

import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

W, H, S = 1280, 720, 2
GLOW_ON = True  # set False to switch the glow off everywhere

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
WHITE = (255, 255, 255, 255)
SOFT = (240, 240, 240, 255)


def _font(name, size):
    for n in (name, "font2.ttf", "font.ttf"):
        try:
            return ImageFont.truetype(os.path.join(ASSETS, n), int(size * S))
        except Exception:
            continue
    return ImageFont.load_default()


def _fit_text(draw, text, font, max_w):
    text = str(text or "").strip() or "Unknown"
    if draw.textlength(text, font=font) <= max_w * S:
        return text
    while text and draw.textlength(text + "...", font=font) > max_w * S:
        text = text[:-1]
    return text.rstrip() + "..."


def _p(x, y):
    return (x * S, y * S)


def _poly(pts, ox=0.0, oy=0.0, k=1.0):
    return [((ox + x * k) * S, (oy + y * k) * S) for x, y in pts]


# ---------------------------------------------------------------- background
def _background(img):
    small = ImageOps.fit(img.convert("RGB"), (W // 4, H // 4))
    bg = small.filter(ImageFilter.GaussianBlur(14)).resize((W * S, H * S), Image.LANCZOS)
    gray = ImageOps.grayscale(bg).convert("RGB")
    bg = Image.blend(bg, gray, 0.78)
    bg = ImageEnhance.Brightness(bg).enhance(0.62)
    bg = ImageEnhance.Contrast(bg).enhance(0.9)

    grad = Image.new("L", (1, H * S))
    for y in range(H * S):
        t = y / (H * S)
        if t < 0.27:
            a = 255 * (1 - t / 0.27) ** 1.4
        elif t > 0.73:
            a = 255 * ((t - 0.73) / 0.27) ** 1.4
        else:
            a = 0
        grad.putpixel((0, y), int(a))
    mask = grad.resize((W * S, H * S))
    return Image.composite(Image.new("RGB", (W * S, H * S), (0, 0, 0)), bg, mask)


def _glow(base, layer, radius, strength):
    g = layer.filter(ImageFilter.GaussianBlur(radius * S))
    a = g.split()[3].point(lambda v: min(255, int(v * strength)))
    g.putalpha(a)
    base.alpha_composite(g)


# ---------------------------------------------------------------- icons
def _star(d, cx, cy, ro, ri, color, w):
    pts = []
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        r = ro if i % 2 == 0 else ri
        pts.append(((cx + r * math.cos(ang)) * S, (cy + r * math.sin(ang)) * S))
    d.line(pts + [pts[0]], fill=color, width=int(w * S), joint="curve")


def _arc_up(d, box, color, w, a0=125, a1=55):
    x0, y0, x1, y1 = [v * S for v in box]
    d.arc((x0, y0, x1, y1), start=a0, end=360, fill=color, width=int(w * S))
    d.arc((x0, y0, x1, y1), start=0, end=a1, fill=color, width=int(w * S))


def _speaker(d, ox, oy, k, color, waves):
    d.polygon(_poly([(3, 9), (8, 9), (13, 5), (13, 19), (8, 15), (3, 15)], ox, oy, k), fill=color)
    if waves:
        cx, cy = (ox + 12 * k) * S, (oy + 12 * k) * S
        for r in (5.5 * k, 9.5 * k):
            R = r * S
            d.arc((cx - R, cy - R, cx + R, cy + R), start=-50, end=50, fill=color, width=int(1.8 * S))


def _ui(d, G, title, artist, duration, f_title):
    """Draw every bright element. G=True -> pure white (used as the glow source)."""
    c = (lambda col: WHITE) if G else (lambda col: col)

    # title
    d.text(_p(718, 126), title, font=f_title, fill=c(WHITE))

    # star + dots
    _star(d, 1096, 164, 11.5, 5.0, c((232, 232, 232, 255)), 2.0)
    for dx in (-8, 0, 8):
        x, y, r = (1164 + dx) * S, 164 * S, 2.4 * S
        d.ellipse((x - r, y - r, x + r, y + r), fill=c((232, 232, 232, 255)))

    # progress fill
    d.rounded_rectangle((718 * S, 224 * S, 1116 * S, 234 * S), radius=5 * S, fill=WHITE)

    # transport: rewind, pause, forward
    ctl = c(SOFT)
    for pts in ([(799, 345), (775, 360), (799, 375)], [(825, 345), (801, 360), (825, 375)],
                [(1105, 345), (1129, 360), (1105, 375)], [(1079, 345), (1103, 360), (1079, 375)]):
        sp = [(x * S, y * S) for x, y in pts]
        d.polygon(sp, fill=ctl)
        d.line(sp + [sp[0]], fill=ctl, width=3 * S, joint="curve")
    d.rounded_rectangle((930 * S, 331 * S, 946 * S, 389 * S), radius=4 * S, fill=ctl)
    d.rounded_rectangle((958 * S, 331 * S, 974 * S, 389 * S), radius=4 * S, fill=ctl)

    # volume fill + speakers
    d.rounded_rectangle((755 * S, 479 * S, 837 * S, 489 * S), radius=5 * S, fill=WHITE)
    _speaker(d, 720, 474, 0.833, c((240, 240, 240, 255)), False)
    _speaker(d, 1156, 474, 0.917, c((240, 240, 240, 255)), True)

    # bottom icons
    ic = c((232, 232, 232, 255))
    # lyrics bubble
    ox, oy = 818, 550
    d.rounded_rectangle(((ox + 2) * S, (oy + 3) * S, (ox + 46) * S, (oy + 31) * S), radius=5 * S, outline=ic, width=3 * S)
    d.polygon(_poly([(24, 31), (12, 41), (12, 31)], ox, oy), fill=ic)
    for qx in (15, 29):
        x, y, r = (ox + qx) * S, (oy + 16) * S, 3.2 * S
        d.ellipse((x - r, y - r, x + r, y + r), fill=ic)
        d.line([(x + 2.4 * S, y), (x - 1.0 * S, y + 6.5 * S)], fill=ic, width=int(2.2 * S))
    # airplay
    ox, oy = 928, 549
    _arc_up(d, (ox + 6, oy + 4, ox + 42, oy + 40), ic, 3)
    _arc_up(d, (ox + 14, oy + 12, ox + 34, oy + 32), ic, 3)
    d.polygon(_poly([(24, 28), (12, 45), (36, 45)], ox, oy), fill=ic)
    # queue list
    ox, oy = 1032, 553
    for ly in (5, 19, 33):
        r = 1.9 * S
        d.ellipse(((ox + 4) * S - r, (oy + ly) * S - r, (ox + 4) * S + r, (oy + ly) * S + r), fill=ic)
        d.line([((ox + 14) * S, (oy + ly) * S), ((ox + 44) * S, (oy + ly) * S)], fill=ic, width=int(3.4 * S))
        for ex in (14, 44):
            rr = 1.7 * S
            d.ellipse(((ox + ex) * S - rr, (oy + ly) * S - rr, (ox + ex) * S + rr, (oy + ly) * S + rr), fill=ic)


def render_card(thumb, title, artist, duration):
    base = _background(thumb).convert("RGBA")
    f_title = _font("pc_bold.ttf", 44)
    f_artist = _font("pc_semibold.ttf", 28)
    f_time = _font("pc_semibold.ttf", 21)

    probe = ImageDraw.Draw(base)
    title = _fit_text(probe, title, f_title, 340)
    artist = _fit_text(probe, artist, f_artist, 440)

    # album art: black rounded square, image fitted to its width
    art = Image.new("RGBA", (500 * S, 500 * S), (0, 0, 0, 255))
    pic = ImageOps.fit(thumb.convert("RGB"), (500 * S, 375 * S), centering=(0.5, 0.5))
    art.paste(pic, (0, 62 * S))
    mask = Image.new("L", art.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 500 * S - 1, 500 * S - 1), radius=48 * S, fill=255)

    halo = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(halo).rounded_rectangle((114 * S, 110 * S, 614 * S, 610 * S), radius=48 * S, fill=WHITE)
    if GLOW_ON:
        g = halo.filter(ImageFilter.GaussianBlur(26 * S))
        g.putalpha(g.split()[3].point(lambda v: int(v * 0.30)))
        base.alpha_composite(g)
    base.paste(art, (114 * S, 110 * S), mask)

    d = ImageDraw.Draw(base)
    # static (non glowing) parts
    d.ellipse((1073 * S, 141 * S, 1119 * S, 187 * S), fill=(150, 95, 95, 140))
    d.ellipse((1141 * S, 141 * S, 1187 * S, 187 * S), fill=(120, 120, 120, 140))
    d.text(_p(718, 182), artist, font=f_artist, fill=(255, 255, 255, 140))
    d.rounded_rectangle((718 * S, 224 * S, 1186 * S, 234 * S), radius=5 * S, fill=(255, 255, 255, 80))
    d.text(_p(718, 246), "0:10", font=f_time, fill=(255, 255, 255, 170))
    dur = str(duration or "0:00")
    d.text((1186 * S - d.textlength(dur, font=f_time), 246 * S), dur, font=f_time, fill=(255, 255, 255, 215))
    d.rounded_rectangle((755 * S, 479 * S, 1137 * S, 489 * S), radius=5 * S, fill=(255, 200, 205, 140))

    if GLOW_ON:
        gl = Image.new("RGBA", base.size, (0, 0, 0, 0))
        _ui(ImageDraw.Draw(gl), True, title, artist, duration, f_title)
        _glow(base, gl, 9, 1.0)
        _glow(base, gl, 3, 0.9)
        # soft halo on the two round buttons
        hb = Image.new("RGBA", base.size, (0, 0, 0, 0))
        hd = ImageDraw.Draw(hb)
        for x0 in (1073, 1141):
            hd.ellipse((x0 * S, 141 * S, (x0 + 46) * S, 187 * S), fill=WHITE)
        g = hb.filter(ImageFilter.GaussianBlur(10 * S))
        g.putalpha(g.split()[3].point(lambda v: int(v * 0.28)))
        base.alpha_composite(g)

    _ui(ImageDraw.Draw(base), False, title, artist, duration, f_title)
    return base.convert("RGB").resize((W, H), Image.LANCZOS)


# ---------------------------------------------------------------- data + public API
async def _fetch(videoid):
    from youtubesearchpython.__future__ import VideosSearch

    title, artist, duration = "Unknown Title", "Unknown Artist", "0:00"
    try:
        data = await VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1).next()
        r = data["result"][0]
        title = str(r.get("title") or title)
        artist = str((r.get("channel") or {}).get("name") or artist)
        duration = str(r.get("duration") or duration)
    except Exception as e:
        print(f"[PLAYERCARD] info fetch failed: {e}")

    thumb = None
    for name in ("hqdefault", "mqdefault"):
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as s:
                async with s.get(f"https://i.ytimg.com/vi/{videoid}/{name}.jpg") as resp:
                    if resp.status == 200:
                        thumb = Image.open(BytesIO(await resp.read())).convert("RGB")
                        break
        except Exception as e:
            print(f"[PLAYERCARD] thumb fetch failed: {e}")
    if thumb is None:
        thumb = Image.new("RGB", (480, 360), (40, 40, 48))
    return title, artist, duration, thumb


async def make_player_card(videoid, user_id=None):
    os.makedirs("cache", exist_ok=True)
    out = f"cache/pc_{videoid}.png"
    if os.path.exists(out):
        return out
    try:
        title, artist, duration, thumb = await _fetch(videoid)
        loop = asyncio.get_running_loop()
        img = await loop.run_in_executor(None, render_card, thumb, title, artist, duration)
        img.save(out, "PNG")
        return out
    except Exception as e:
        print(f"[PLAYERCARD] render failed: {e}")
        return None
