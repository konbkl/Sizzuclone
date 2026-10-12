"""Glass player card (1280x720) for CLONE bots.

    path = await make_clone_card(videoid)

Blurred song art as background, a frosted glass card with a glowing gradient
border, album art with its own glow, progress bar and a row of control icons.
Everything is drawn at 2x and scaled down for smooth edges.
"""

import asyncio
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

W, H, S = 1280, 720, 2
ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

CARD = (220, 140, 1060, 580)      # glass card
ART = (260, 190, 600, 530)        # album art
WHITE = (255, 255, 255, 255)


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


def _box(b):
    return tuple(int(v * S) for v in b)


def _rr_mask(size, box, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle(_box(box), radius=radius * S, fill=255)
    return m


def _ring_mask(size, box, radius, width):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle(_box(box), radius=radius * S, outline=255, width=int(width * S))
    return m


def _hgrad(size, box, stops):
    """Horizontal colour gradient over `box` (design px) using [(pos, (r,g,b)), ...]."""
    x0, _, x1, _ = box
    row = Image.new("RGB", (size[0], 1))
    px = row.load()
    for x in range(size[0]):
        t = (x / S - x0) / max(1, (x1 - x0))
        t = min(1.0, max(0.0, t))
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                k = (t - p0) / max(1e-6, p1 - p0)
                px[x, 0] = tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(3))
                break
    return row.resize(size).convert("RGBA")


def _glow_ring(base, size, box, radius, width, stops, blur, strength):
    ring = _ring_mask(size, box, radius, width)
    grad = _hgrad(size, box, stops)
    glow = grad.copy()
    glow.putalpha(ring.filter(ImageFilter.GaussianBlur(blur * S)).point(lambda v: min(255, int(v * strength))))
    base.alpha_composite(glow)
    crisp = grad.copy()
    crisp.putalpha(ring)
    base.alpha_composite(crisp)


def _background(img):
    small = ImageOps.fit(img.convert("RGB"), (W // 2, H // 2))
    bg = small.filter(ImageFilter.GaussianBlur(7)).resize((W * S, H * S), Image.LANCZOS)
    bg = ImageEnhance.Color(bg).enhance(1.15)
    return ImageEnhance.Brightness(bg).enhance(0.92)


# ---------------------------------------------------------------- icons
def _heart(d, cx, cy, k, color):
    pts = []
    for i in range(60):
        t = math.radians(i * 6)
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append(((cx + x * k) * S, (cy + y * k) * S))
    d.polygon(pts, fill=color)


def _tri(d, pts, color):
    d.polygon([(x * S, y * S) for x, y in pts], fill=color)


def _icons(d, G):
    c = (lambda col: WHITE) if G else (lambda col: col)

    # shuffle (green)
    g = c((60, 255, 160, 255))
    for a, b in (((629, 493), (639, 493)), ((639, 493), (651, 507)), ((651, 507), (655, 507)),
                 ((629, 507), (639, 507)), ((639, 507), (651, 493)), ((651, 493), (655, 493))):
        d.line([(a[0] * S, a[1] * S), (b[0] * S, b[1] * S)], fill=g, width=int(3 * S))
    _tri(d, [(654, 488), (654, 498), (661, 493)], g)
    _tri(d, [(654, 502), (654, 512), (661, 507)], g)

    # repeat (amber)
    o = c((255, 190, 40, 255))
    d.arc((687 * S, 489 * S, 709 * S, 511 * S), start=40, end=340, fill=o, width=int(3 * S))
    _tri(d, [(701, 484), (701, 496), (711, 490)], o)

    # previous, pause, next (white)
    w = c(WHITE)
    d.rectangle((737 * S, 489 * S, 741 * S, 511 * S), fill=w)
    _tri(d, [(755, 489), (755, 511), (742, 500)], w)
    _tri(d, [(769, 489), (769, 511), (756, 500)], w)
    d.rounded_rectangle((800 * S, 489 * S, 806 * S, 511 * S), radius=2 * S, fill=w)
    d.rounded_rectangle((810 * S, 489 * S, 816 * S, 511 * S), radius=2 * S, fill=w)
    d.rectangle((875 * S, 489 * S, 879 * S, 511 * S), fill=w)
    _tri(d, [(861, 489), (861, 511), (874, 500)], w)
    _tri(d, [(847, 489), (847, 511), (860, 500)], w)

    # heart (red)
    _heart(d, 920, 499, 0.95, c((255, 60, 60, 255)))

    # headphones (white)
    d.arc((962 * S, 488 * S, 990 * S, 516 * S), start=180, end=360, fill=w, width=int(3.2 * S))
    d.rounded_rectangle((960 * S, 500 * S, 968 * S, 513 * S), radius=3 * S, fill=w)
    d.rounded_rectangle((984 * S, 500 * S, 992 * S, 513 * S), radius=3 * S, fill=w)


def render_card(thumb, title, artist, duration):
    size = (W * S, H * S)
    bg = _background(thumb)
    base = bg.convert("RGBA")

    # frosted glass card
    cmask = _rr_mask(size, CARD, 46)
    frost = bg.filter(ImageFilter.GaussianBlur(14 * S)).convert("RGBA")
    frost = Image.alpha_composite(frost, Image.new("RGBA", size, (0, 0, 0, 95)))
    base.paste(frost, (0, 0), cmask)

    card_stops = [(0.0, (88, 160, 214)), (0.30, (186, 128, 165)), (0.50, (140, 214, 20)),
                  (0.78, (150, 205, 35)), (1.0, (208, 122, 132))]
    _glow_ring(base, size, CARD, 46, 5, card_stops, 9, 0.9)

    # album art
    art_box = ART
    amask = _rr_mask(size, art_box, 30)
    pic = ImageOps.fit(thumb.convert("RGB"), ((ART[2] - ART[0]) * S, (ART[3] - ART[1]) * S), centering=(0.4, 0.5))
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    layer.paste(pic, (ART[0] * S, ART[1] * S))
    # soft dark edge inside the art
    edge = Image.new("L", size, 0)
    ImageDraw.Draw(edge).rounded_rectangle(_box(art_box), radius=30 * S, outline=255, width=int(14 * S))
    edge = edge.filter(ImageFilter.GaussianBlur(7 * S))
    shade = Image.new("RGBA", size, (0, 0, 0, 0))
    shade.putalpha(edge.point(lambda v: int(v * 0.55)))
    layer = Image.alpha_composite(layer, shade)
    layer.putalpha(ImageChops.multiply(layer.split()[3], amask))
    base.alpha_composite(layer)
    art_stops = [(0.0, (100, 160, 215)), (0.5, (130, 190, 120)), (1.0, (150, 215, 30))]
    _glow_ring(base, size, art_box, 30, 4, art_stops, 6, 0.8)

    d = ImageDraw.Draw(base)
    f_title = _font("cc_regular.ttf", 33)
    f_artist = _font("cc_bold.ttf", 23)
    f_time = _font("cc_bold.ttf", 18)

    t = _fit_text(d, str(title or "").upper(), f_title, 400)
    d.text((640 * S, 236 * S), t, font=f_title, fill=(255, 255, 255, 255))
    a = _fit_text(d, artist, f_artist, 400)
    d.text((640 * S, 299 * S), a, font=f_artist, fill=(222, 222, 222, 255))

    # progress bar
    d.rounded_rectangle((640 * S, 397 * S, 1020 * S, 403 * S), radius=3 * S, fill=(205, 205, 205, 255))
    d.rounded_rectangle((640 * S, 397 * S, 727 * S, 403 * S), radius=3 * S, fill=(124, 210, 28, 255))
    knob = Image.new("RGBA", size, (0, 0, 0, 0))
    kd = ImageDraw.Draw(knob)
    kd.ellipse(((727 - 9) * S, (400 - 9) * S + 2 * S, (727 + 9) * S, (400 + 9) * S + 2 * S), fill=(0, 0, 0, 90))
    base.alpha_composite(knob.filter(ImageFilter.GaussianBlur(3 * S)))
    d = ImageDraw.Draw(base)
    d.ellipse(((727 - 8) * S, (400 - 8) * S, (727 + 8) * S, (400 + 8) * S), fill=WHITE)

    d.text((640 * S, 425 * S), "01:00", font=f_time, fill=WHITE)
    dur = str(duration or "0:00")
    d.text((1020 * S - d.textlength(dur, font=f_time), 425 * S), dur, font=f_time, fill=WHITE)

    # controls with a soft glow
    gl = Image.new("RGBA", size, (0, 0, 0, 0))
    _icons(ImageDraw.Draw(gl), True)
    g = gl.filter(ImageFilter.GaussianBlur(5 * S))
    g.putalpha(g.split()[3].point(lambda v: int(v * 0.55)))
    base.alpha_composite(g)
    _icons(ImageDraw.Draw(base), False)

    # small badge, top right
    badge = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(badge).rounded_rectangle(_box((1178, 24, 1248, 94)), radius=16 * S, fill=(255, 255, 255, 215))
    base.alpha_composite(badge)
    bd = ImageDraw.Draw(base)
    bd.ellipse((1203 * S, 49 * S, 1223 * S, 69 * S), outline=(236, 140, 160, 255), width=int(3 * S))

    return base.convert("RGB").resize((W, H), Image.LANCZOS)


async def make_clone_card(videoid, user_id=None):
    out_dir = "cache"
    os.makedirs(out_dir, exist_ok=True)
    out = f"{out_dir}/cc_{videoid}.png"
    if os.path.exists(out):
        return out
    try:
        from SHIVMUSIC.utils.playercard import _fetch

        title, artist, duration, thumb = await _fetch(videoid)
        loop = asyncio.get_running_loop()
        img = await loop.run_in_executor(None, render_card, thumb, title, artist, duration)
        img.save(out, "PNG")
        return out
    except Exception as e:
        print(f"[CLONECARD] render failed: {e}")
        return None
              
