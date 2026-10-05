"""Vibe-aware autoplay engine.

Old behaviour: take the last song, grab its YouTube Mix and pick a *random*
entry. Result: language / mood drifted (Punjabi -> English -> remix -> bhajan).

New behaviour:
  1. Every played track is fed to ``note_played`` so each chat builds a
     *vibe profile*: language, mood tags, energy, artist/film keywords.
  2. Candidates come from several sources at once
        - the Mix of the song that just finished (keeps the flow),
        - the Mix of a song the humans actually requested ("anchor", so
          autoplay cannot drift away from what the group asked for),
        - a profile-based search (artist + language + mood) as top-up.
  3. Candidates are filtered (covers, karaoke, reactions, jukeboxes, shorts,
     duplicates / same song re-uploaded) and *scored* against the profile.
  4. A weighted pick among the best few keeps it fresh but always on-vibe.
  5. A small per-chat pool is cached, so the next song starts much faster.

Pure helpers (analyze / score / rank) do no network access, so they are
unit-testable.
"""

import asyncio
import os
import random
import re
import time
from difflib import SequenceMatcher
from typing import Optional

import aiohttp
import yt_dlp
from py_yt import VideosSearch

# =========================================================
# CONFIG
# =========================================================
_HISTORY_LIMIT = 80          # remembered video ids per chat
_TITLE_HISTORY_LIMIT = 40    # remembered normalized titles per chat
_ANCHOR_LIMIT = 4            # how many human-picked songs shape the vibe
_POOL_TTL = 20 * 60          # seconds a cached pool stays fresh
_POOL_SIZE = 12
_MIN_SECONDS = 60
_MAX_SECONDS = 12 * 60       # single songs only, no jukeboxes
_TOP_PICK = 4                # choose among the best N candidates

AUTOPLAY_MARK = "ᴀᴜᴛᴏᴘʟᴀʏ"   # appears in queue item "by" for autoplay tracks

# =========================================================
# VIBE KNOWLEDGE
# =========================================================
_NOISE_WORDS = {
    "official", "video", "videos", "song", "songs", "audio", "lyrical", "lyrics",
    "lyric", "full", "hd", "4k", "1080p", "new", "latest", "music", "version",
    "out", "now", "hit", "hits", "feat", "ft", "featuring", "the", "an",
    "of", "in", "on", "and", "with", "from", "by", "to", "for", "is", "se",
    "ka", "ki", "ke", "ko", "hai", "ho", "main", "mein", "tum", "mera",
    "meri", "mere", "yeh", "jo", "hi", "bhi", "movie",
    "film", "soundtrack", "original", "studio", "visualizer", "visualiser",
    "teaser", "promo", "prod", "produced", "records", "record", "label",
    "presents", "present", "series", "tseries", "vevo", "topic", "youtube",
    "channel", "bass", "boosted", "remix", "slowed", "reverb", "lofi",
}

# language -> (title keyword regex, unicode script regex)
_LANGS = {
    "punjabi": (r"\b(punjabi|panjabi|sidhu|moose ?wala|diljit|ap dhillon|karan aujla|"
                r"amrit maan|babbu maan|gurdas|jass manak|sharry mann|ammy virk|"
                r"shubh|gippy|b praak|kaka|harnoor|jazzy b|hardy sandhu)\b", r"[\u0A00-\u0A7F]"),
    "haryanvi": (r"\b(haryanvi|masoom sharma|renuka panwar|sapna choudhary|raju punjabi|"
                 r"ajay hooda|pranjal dahiya|diler kharkiya)\b", None),
    "bhojpuri": (r"\b(bhojpuri|pawan singh|khesari|neelkamal|dinesh lal|nirahua|"
                 r"shilpi raj|samar singh|arvind akela)\b", None),
    "rajasthani": (r"\b(rajasthani|marwadi|ghoomar|gori nagori)\b", None),
    "tamil": (r"\b(tamil|anirudh|yuvan)\b", r"[\u0B80-\u0BFF]"),
    "telugu": (r"\b(telugu|devi sri prasad|dsp|thaman|pushpa)\b", r"[\u0C00-\u0C7F]"),
    "malayalam": (r"\b(malayalam|mollywood)\b", r"[\u0D00-\u0D7F]"),
    "kannada": (r"\b(kannada|sandalwood)\b", r"[\u0C80-\u0CFF]"),
    "bengali": (r"\b(bengali|bangla)\b", r"[\u0980-\u09FF]"),
    "marathi": (r"\b(marathi|ajay atul)\b", None),
    "gujarati": (r"\b(gujarati|garba)\b", r"[\u0A80-\u0AFF]"),
    "arabic": (r"\b(arabic|khaleeji|nasheed|nashid)\b", r"[\u0600-\u06FF]"),
    "korean": (r"\b(k-?pop|korean|bts|blackpink|stray kids)\b", r"[\uAC00-\uD7AF]"),
    "english": (r"\b(english|taylor swift|ed sheeran|the weeknd|billie eilish|dua lipa|"
                r"justin bieber|imagine dragons|coldplay|post malone|eminem|drake|"
                r"bruno mars|ariana grande|maroon 5|adele|selena gomez)\b", None),
    "hindi": (r"\b(hindi|bollywood|arijit|atif aslam|jubin|shreya ghoshal|sonu nigam|"
              r"neha kakkar|badshah|honey singh|darshan raval|armaan malik|"
              r"kumar sanu|udit narayan|alka yagnik|kishore kumar|lata|rafi|mohit chauhan|"
              r"vishal mishra|tulsi kumar|palak muchhal|guru randhawa|"
              r"raftaar|divine|emiway)\b", r"[\u0900-\u097F]"),
}

# Languages that sit close together (a Hindi song after a Punjabi one is fine,
# an English song is not).
_RELATED = [
    {"hindi", "punjabi", "haryanvi", "bhojpuri", "rajasthani", "marathi", "gujarati"},
    {"tamil", "telugu", "malayalam", "kannada"},
]

# mood / style tags -> regex
_TAGS = {
    "lofi": r"\b(lo-?fi|chill|study|relax(ing)?|calm)\b",
    "slowed": r"\b(slowed|reverb|sped ?up)\b",
    "remix": r"\b(remix|dj|club mix|edm|dance mix|bounce)\b",
    "phonk": r"\b(phonk|drift)\b",
    "sad": r"\b(sad|dard|bewafa|bewafai|breakup|judai|judaai|tanha|alvida|rula|rona|"
           r"heartbreak|broken|cry|tears|dukh|yaad|tadap|toota)\b",
    "romantic": r"\b(love|ishq|pyar|pyaar|mohabbat|romantic|dil|ishqa|dilbar|saajan|"
                r"sanam|jaan|kiss)\b",
    "party": r"\b(party|dance|nagin|club|nacho|dhol|bhangra|garba|dandiya|"
             r"wedding|shaadi|baraat|mashup)\b",
    "devotional": r"\b(bhajan|aarti|bhakti|mantra|chalisa|shiv|shiva|mahadev|bholenath|"
                  r"krishna|kanha|hanuman|ganesh|durga|mata|sai baba|kirtan|"
                  r"shabad|gurbani|naat|qawwali)\b",
    "rap": r"\b(rap|hip ?hop|drill|trap|rapper|diss|cypher|freestyle)\b",
    "retro": r"\b(retro|90s|80s|70s|old|classic|golden|purane|evergreen|vintage|"
             r"kishore|rafi|lata|asha|mukesh|rd burman)\b",
    "ghazal": r"\b(ghazal|jagjit|ghulam ali|mehdi hassan|nusrat|sufi|sufiana)\b",
    "instrumental": r"\b(instrumental|flute|piano|bgm|violin|guitar|saxophone)\b",
    "acoustic": r"\b(acoustic|unplugged|stripped|coke studio|sessions?)\b",
    "attitude": r"\b(attitude|gangster|gangsta|badmash|swag|legend|jatt|jatti|yaari|"
                r"thar|bullet)\b",
}

# energy: + high, - low
_ENERGY = {
    "party": 1, "remix": 1, "phonk": 1, "rap": 1, "attitude": 1,
    "lofi": -1, "slowed": -1, "sad": -1, "acoustic": -1, "ghazal": -1,
    "romantic": -0.3, "retro": -0.3, "instrumental": -0.3,
}

# Tags that mean "completely different kind of song" when they don't match.
_STRICT_TAGS = {"devotional", "ghazal", "instrumental", "rap"}

# Non-songs / low quality / wrong format: never autoplay these.
_BAD_TITLE = re.compile(
    r"\b(cover|karaoke|tutorial|how to|reaction|reacts?|review|interview|trailer|"
    r"teaser|making of|behind the scenes|full album|jukebox|nonstop|non-stop|"
    r"live stream|livestream|24/7|podcast|ringtone|whatsapp status|status video|"
    r"shorts|comedy|roast|dialogue|episode|vlog|news|speech|audiobook|"
    r"lecture|asmr|8d audio|10 hours|1 hour|hour loop|compilation)\b",
    re.I,
)

_LABELS = (
    "t-series", "tseries", "t series", "saregama", "zee music", "sony music",
    "tips official", "tips music", "speed records", "lahari", "times music",
    "eros now", "yrf", "vevo", "- topic",
)


# =========================================================
# TEXT HELPERS
# =========================================================
def _norm(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[\(\[\{].*?[\)\]\}]", " ", text)  # drop (...) [...]
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(text: str) -> set:
    return {
        w for w in _norm(text).split()
        if len(w) > 2 and w not in _NOISE_WORDS and not w.isdigit()
    }


def song_key(title: str) -> str:
    """Normalized 'which song is this' key: all meaningful words, no upload noise."""
    return " ".join(w for w in _norm(title).split() if w not in _NOISE_WORDS)


def parse_duration(value) -> int:
    """'3:45' / '1:02:03' / 225 / None -> seconds (0 if unknown/live)."""
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    try:
        nums = [int(p) for p in str(value).strip().split(":")]
    except ValueError:
        return 0
    sec = 0
    for n in nums:
        sec = sec * 60 + n
    return sec


def format_duration(seconds: int) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


# =========================================================
# VIBE PROFILE
# =========================================================
def analyze(title: str, channel: str = "") -> dict:
    """Extract language / tags / energy / keywords from a title (+ channel)."""
    raw = title or ""
    text = f"{raw} {channel or ''}".lower()

    lang_scores = {}
    for lang, (kw, script) in _LANGS.items():
        score = 0
        if kw and re.search(kw, text, re.I):
            score += 2
        if script and re.search(script, raw):
            score += 3
        if score:
            lang_scores[lang] = score
    lang = max(lang_scores, key=lang_scores.get) if lang_scores else None

    tags = {tag for tag, rx in _TAGS.items() if re.search(rx, text, re.I)}
    energy = sum(_ENERGY.get(t, 0) for t in tags)

    tokens = _tokens(raw)
    ch = (channel or "").strip().lower()
    if ch and not any(label in ch for label in _LABELS):
        tokens |= _tokens(channel)

    return {"lang": lang, "tags": tags, "energy": energy, "tokens": tokens}


def _blend(profiles: list) -> dict:
    """Combine several profiles (recent human picks, oldest -> newest)."""
    if not profiles:
        return {"lang": None, "langs": {}, "tags": set(), "energy": 0.0,
                "tokens": {}, "total_w": 0.0}

    langs, tag_w, tok_w = {}, {}, {}
    energy, total_w = 0.0, 0.0
    for i, p in enumerate(profiles):
        w = 1.0 + 0.6 * i  # newer picks matter more
        total_w += w
        if p["lang"]:
            langs[p["lang"]] = langs.get(p["lang"], 0) + w
        for t in p["tags"]:
            tag_w[t] = tag_w.get(t, 0) + w
        for t in p["tokens"]:
            tok_w[t] = tok_w.get(t, 0) + w
        energy += p["energy"] * w

    return {
        "lang": max(langs, key=langs.get) if langs else None,
        "langs": langs,
        "tags": {t for t, w in tag_w.items() if w >= total_w * 0.4},
        "energy": energy / total_w,
        "tokens": tok_w,
        "total_w": total_w,
    }


# =========================================================
# PER-CHAT STATE (in-memory)
# =========================================================
_played_ids: dict = {}     # chat_id -> [vidid]
_played_titles: dict = {}  # chat_id -> [song_key]
_anchors: dict = {}        # chat_id -> [{vidid,title,seconds,profile}] human picks
_last_auto: dict = {}      # chat_id -> last autoplayed song_key
_pool: dict = {}           # chat_id -> {"ts": float, "items": [...]}
_anchor_rr: dict = {}      # chat_id -> round-robin counter
_last_yt: dict = {}         # chat_id -> {vidid,title} last real YouTube track (seed fallback)
_YT_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def remember_played(chat_id: int, vidid: str):
    if not vidid:
        return
    hist = _played_ids.setdefault(chat_id, [])
    if vidid in hist:
        hist.remove(vidid)
    hist.append(vidid)
    if len(hist) > _HISTORY_LIMIT:
        del hist[: len(hist) - _HISTORY_LIMIT]


def clear_history(chat_id: int):
    _played_ids.pop(chat_id, None)
    _played_titles.pop(chat_id, None)
    _pool.pop(chat_id, None)


def reset_chat(chat_id: int):
    """Forget everything (use when a chat's session fully ends)."""
    for store in (_played_ids, _played_titles, _anchors, _last_auto, _pool, _anchor_rr, _last_yt):
        store.pop(chat_id, None)


def note_played(chat_id: int, title: str, vidid: str = None, by: str = "",
                channel: str = "", seconds: int = 0):
    """Feed every played track here so the chat's vibe is learned."""
    if not title:
        return
    remember_played(chat_id, vidid)
    if vidid and _YT_ID.match(str(vidid)):
        _last_yt[chat_id] = {"vidid": vidid, "title": title}
    key = song_key(title)
    if key:
        titles = _played_titles.setdefault(chat_id, [])
        if key in titles:
            titles.remove(key)
        titles.append(key)
        if len(titles) > _TITLE_HISTORY_LIMIT:
            del titles[: len(titles) - _TITLE_HISTORY_LIMIT]

    if AUTOPLAY_MARK in (by or ""):
        _last_auto[chat_id] = key
        return
    # A human asked for this -> it shapes the vibe.
    anchors = _anchors.setdefault(chat_id, [])
    anchors[:] = [a for a in anchors if a["vidid"] != vidid or not vidid]
    anchors.append({"vidid": vidid, "title": title, "seconds": seconds,
                    "profile": analyze(title, channel)})
    if len(anchors) > _ANCHOR_LIMIT:
        del anchors[: len(anchors) - _ANCHOR_LIMIT]
    _pool.pop(chat_id, None)  # new taste -> rebuild candidate pool


# =========================================================
# SCORING
# =========================================================
def _is_dup(key: str, known: list) -> bool:
    """Same song, different upload (slowed / lyrical / re-upload / reordered title)."""
    if not key:
        return False
    words = set(key.split())
    for k in known:
        if not k:
            continue
        if key == k:
            return True
        if len(key) > 6 and len(k) > 6 and SequenceMatcher(None, key, k).ratio() >= 0.82:
            return True
        other = set(k.split())
        small, large = (words, other) if len(words) <= len(other) else (other, words)
        if len(small) >= 3 and small <= large:
            return True
    return False


def _lang_relation(cand_lang: str, vibe: dict) -> float:
    """+ for same / requested language, small - for related, big - for foreign."""
    if cand_lang == vibe["lang"]:
        return 4.0
    if cand_lang in (vibe.get("langs") or {}):
        return 2.0
    for group in _RELATED:
        if cand_lang in group and vibe["lang"] in group:
            return -1.0
    return -6.0


def score_candidate(cand: dict, vibe: dict, chat_id: int = 0,
                    anchor_seconds: int = 0) -> Optional[float]:
    """Vibe score, or None when the candidate must be rejected."""
    title = cand.get("title") or ""
    sec = cand.get("duration_sec", 0)

    if _BAD_TITLE.search(title):
        return None
    if not sec or sec < _MIN_SECONDS:  # live streams / shorts / unknown
        return None
    max_sec = max(_MAX_SECONDS, anchor_seconds + 120) if anchor_seconds > _MAX_SECONDS else _MAX_SECONDS
    if sec > max_sec:
        return None

    p = analyze(title, cand.get("channel", ""))
    has_vibe = bool(vibe.get("total_w"))
    score = 0.0

    # ---- language (biggest signal) ----
    if vibe.get("lang") and p["lang"]:
        score += _lang_relation(p["lang"], vibe)
    elif vibe.get("lang"):
        score += 0.3  # unknown language: benefit of the doubt

    # ---- mood tags ----
    vt, ct = vibe.get("tags", set()), p["tags"]
    score += 1.6 * len(vt & ct)
    if has_vibe:
        for t in _STRICT_TAGS:
            if t in ct and t not in vt:
                score -= 3.5   # candidate is devotional/ghazal/rap/... but vibe isn't
            elif t in vt and t not in ct:
                score -= 1.0   # can't tell: mild penalty only
        for t in ("remix", "slowed", "lofi", "phonk"):
            if t in ct and t not in vt and vt:
                score -= 1.2

    # ---- energy closeness ----
    score -= 0.9 * abs(p["energy"] - vibe.get("energy", 0.0))

    # ---- artist / film / keyword overlap ----
    tok_w = vibe.get("tokens") or {}
    total_w = vibe.get("total_w") or 1.0
    overlap = sum(tok_w[t] / total_w for t in p["tokens"] if t in tok_w)
    score += min(overlap, 2.0) * 1.8

    # ---- duration closeness ----
    if anchor_seconds:
        ratio = sec / anchor_seconds
        if ratio > 2.2 or ratio < 0.4:
            score -= 1.0

    # ---- don't hammer near-identical titles back to back ----
    last = _last_auto.get(chat_id)
    if last and SequenceMatcher(None, song_key(title), last).ratio() > 0.6:
        score -= 1.5

    # ---- clean official upload bonus ----
    if re.search(r"\b(official|video song|lyrical|audio)\b", title, re.I):
        score += 0.4

    return score


def rank_candidates(cands: list, chat_id: int) -> list:
    """Filter + score + dedupe a raw candidate list. Best first."""
    anchors = _anchors.get(chat_id, [])
    vibe = _blend([a["profile"] for a in anchors])
    anchor_secs = (anchors[-1].get("seconds") or 0) if anchors else 0

    played_ids = set(_played_ids.get(chat_id, []))
    known_keys = list(_played_titles.get(chat_id, []))

    seen_ids, seen_keys, scored = set(), [], []
    for c in cands:
        vid = c.get("vidid")
        if not vid or vid in seen_ids or vid in played_ids:
            continue
        key = song_key(c.get("title", ""))
        if _is_dup(key, known_keys) or _is_dup(key, seen_keys):
            continue
        s = score_candidate(c, vibe, chat_id, anchor_secs)
        if s is None:
            continue
        seen_ids.add(vid)
        seen_keys.append(key)
        scored.append((s, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [dict(c, score=round(s, 2)) for s, c in scored]


def weighted_pick(items: list) -> Optional[dict]:
    """Pick among the best few: on-vibe but not repetitive."""
    if not items:
        return None
    top = items[:_TOP_PICK]
    best = top[0]["score"]
    weights = [max(0.15, 1.0 - (best - it["score"]) * 0.25) for it in top]
    return random.choices(top, weights=weights, k=1)[0]


# =========================================================
# CANDIDATE SOURCES (network)
# =========================================================
def _cookie_file():
    folder = os.path.join(os.getcwd(), "SHIVMUSIC", "assets")
    try:
        files = [f for f in os.listdir(folder) if f.endswith(".txt")]
    except OSError:
        return None
    return os.path.join(folder, random.choice(files)) if files else None


def _fetch_mix_sync(video_id: str, limit: int = 25) -> list:
    opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "playlistend": limit,
        "no_warnings": True,
    }
    cookie = _cookie_file()
    if cookie:
        opts["cookiefile"] = cookie
    url = f"https://www.youtube.com/watch?v={video_id}&list=RD{video_id}"
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return (info or {}).get("entries") or []


def _from_mix_entry(e: dict) -> Optional[dict]:
    if not e:
        return None
    vid, title = e.get("id"), e.get("title")
    if not (vid and title):
        return None
    dur = parse_duration(e.get("duration"))
    return {
        "vidid": vid,
        "title": title,
        "channel": e.get("channel") or e.get("uploader") or "",
        "link": f"https://www.youtube.com/watch?v={vid}",
        "duration_sec": dur,
        "duration_min": format_duration(dur) if dur else "Live",
        "thumb": e.get("thumbnail") or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
    }


def _from_search_result(v: dict) -> Optional[dict]:
    vid, title, dur = v.get("id"), v.get("title"), v.get("duration")
    if not (vid and title and dur):
        return None
    sec = parse_duration(dur)
    thumbs = v.get("thumbnails") or []
    ch = v.get("channel")
    ch = ch.get("name") if isinstance(ch, dict) else (ch or "")
    return {
        "vidid": vid,
        "title": title,
        "channel": ch,
        "link": v.get("link") or f"https://www.youtube.com/watch?v={vid}",
        "duration_sec": sec,
        "duration_min": format_duration(sec),
        "thumb": (thumbs[0].get("url", "").split("?")[0] if thumbs else None),
    }


# ---- Fast path: YouTube InnerTube /next (same call the Go bot uses) ----
_YT_NEXT_URL = "https://www.youtube.com/youtubei/v1/next?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
_YT_CONTEXT = {"client": {"clientName": "WEB", "clientVersion": "2.20240229.01.00", "hl": "en"}}
_LABEL_RE = re.compile(r"(\d+)\s*(hour|minute|second)", re.I)


def _dig(node, *path):
    for key in path:
        if isinstance(key, int):
            if not isinstance(node, list) or key >= len(node):
                return None
            node = node[key]
        else:
            if not isinstance(node, dict):
                return None
            node = node.get(key)
        if node is None:
            return None
    return node


def _innertube_duration(v: dict) -> int:
    txt = _dig(v, "lengthText", "simpleText")
    if txt:
        return parse_duration(txt)
    label = _dig(v, "lengthText", "accessibility", "accessibilityData", "label") or ""
    mult = {"hour": 3600, "minute": 60, "second": 1}
    return sum(int(n) * mult[u.lower()] for n, u in _LABEL_RE.findall(label))


def _from_innertube_entry(item: dict) -> Optional[dict]:
    v = (item or {}).get("playlistPanelVideoRenderer")
    if not v:
        return None
    vid = v.get("videoId")
    title = _dig(v, "title", "simpleText") or _dig(v, "title", "runs", 0, "text")
    if not (vid and title):
        return None
    dur = _innertube_duration(v)
    return {
        "vidid": vid,
        "title": title,
        "channel": _dig(v, "shortBylineText", "runs", 0, "text") or "",
        "link": f"https://www.youtube.com/watch?v={vid}",
        "duration_sec": dur,
        "duration_min": format_duration(dur) if dur else "Live",
        "thumb": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
    }


async def _mix_innertube(video_id: str) -> list:
    payload = {"context": _YT_CONTEXT, "videoId": video_id, "playlistId": f"RD{video_id}"}
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(_YT_NEXT_URL, json=payload) as resp:
            if resp.status != 200:
                raise RuntimeError(f"innertube status {resp.status}")
            data = await resp.json(content_type=None)
    items = _dig(data, "contents", "twoColumnWatchNextResults", "playlist",
                 "playlist", "contents") or []
    return [c for c in (_from_innertube_entry(i) for i in items) if c]


async def _mix(video_id: str) -> list:
    if not video_id:
        return []
    # 1) fast InnerTube call (~1s, no cookies needed)
    try:
        fast = await _mix_innertube(video_id)
        if len(fast) >= 3:
            return fast
    except Exception as e:
        print(f"[AUTOPLAY INNERTUBE ERROR] {type(e).__name__}: {e}")
    # 2) slow but sturdy fallback: yt-dlp
    loop = asyncio.get_running_loop()
    try:
        entries = await asyncio.wait_for(
            loop.run_in_executor(None, _fetch_mix_sync, video_id, 25), timeout=45
        )
    except Exception as e:
        print(f"[AUTOPLAY MIX ERROR] {type(e).__name__}: {e}")
        return []
    return [c for c in (_from_mix_entry(x) for x in entries) if c]


async def _search(query: str, limit: int = 15) -> list:
    if not query:
        return []
    try:
        data = await asyncio.wait_for(VideosSearch(query, limit=limit).next(), timeout=25)
    except Exception as e:
        print(f"[AUTOPLAY SEARCH ERROR] {type(e).__name__}: {e}")
        return []
    results = data.get("result", []) if isinstance(data, dict) else []
    return [c for c in (_from_search_result(x) for x in results) if c]


def _profile_queries(chat_id: int, seed_title: str) -> list:
    """Search queries built from the chat's vibe (artist + language + mood)."""
    vibe = _blend([a["profile"] for a in _anchors.get(chat_id, [])])
    lang = vibe.get("lang")
    moods = [t for t in ("sad", "romantic", "party", "devotional", "lofi", "slowed",
                         "remix", "phonk", "rap", "retro", "ghazal", "acoustic",
                         "attitude", "instrumental") if t in vibe.get("tags", set())]
    tok_w = vibe.get("tokens") or {}
    top_tokens = [t for t, _ in sorted(tok_w.items(), key=lambda x: -x[1])[:2]]

    qs = []
    if top_tokens:
        qs.append(f"{' '.join(top_tokens)} songs")
    if lang and moods:
        qs.append(f"{lang} {moods[0]} songs")
    elif lang:
        qs.append(f"{lang} songs latest hits")
    if seed_title:
        qs.append(f"songs like {seed_title}")
    return qs[:3]


async def _build_pool(chat_id: int, seed_title: str, seed_vidid: str) -> list:
    anchors = _anchors.get(chat_id, [])

    # Round-robin over human-picked songs so the vibe is a blend of everything
    # requested, not only the newest request.
    anchor_ids = [a["vidid"] for a in anchors if a.get("vidid")]
    rr = _anchor_rr.get(chat_id, 0)
    anchor_pick = anchor_ids[rr % len(anchor_ids)] if anchor_ids else None
    _anchor_rr[chat_id] = rr + 1

    sources = [_mix(seed_vidid)]
    if anchor_pick and anchor_pick != seed_vidid:
        sources.append(_mix(anchor_pick))

    raw = []
    for r in await asyncio.gather(*sources, return_exceptions=True):
        if isinstance(r, list):
            raw.extend(r)

    ranked = rank_candidates(raw, chat_id)
    good = [c for c in ranked if c["score"] > 0]

    # Top up with profile search if the Mix gave too little on-vibe material.
    if len(good) < 4:
        for q in _profile_queries(chat_id, seed_title):
            raw.extend(await _search(q))
            ranked = rank_candidates(raw, chat_id)
            good = [c for c in ranked if c["score"] > 0]
            if len(good) >= 6:
                break

    # Prefer clearly on-vibe; if none, accept the least-bad so it never stalls.
    return (good or ranked)[:_POOL_SIZE]


# =========================================================
# PUBLIC API
# =========================================================
async def fetch_autoplay_track(chat_id: int, seed_title: str, seed_vidid: str = None):
    """Return the next on-vibe track dict, or None.

    Keys: vidid, title, link, duration_min, thumb (+ duration_sec, score).
    """
    # Go-bot style: Mix needs a real YouTube id. If the last song was a
    # Telegram file / Spotify / SoundCloud etc., continue from the last
    # YouTube track that played in this chat instead of giving up.
    if not (seed_vidid and _YT_ID.match(str(seed_vidid))):
        last = _last_yt.get(chat_id)
        if last:
            seed_vidid, seed_title = last["vidid"], last["title"]

    if seed_vidid:
        remember_played(chat_id, seed_vidid)

    # Safety net: if no human pick was ever recorded, learn from the seed.
    if not _anchors.get(chat_id) and seed_title:
        note_played(chat_id, seed_title, seed_vidid)

    state = _pool.get(chat_id)
    fresh = bool(state) and (time.time() - state["ts"] < _POOL_TTL)
    played = set(_played_ids.get(chat_id, []))
    items = [i for i in (state["items"] if fresh else []) if i["vidid"] not in played]

    # Refill when low; the cached pool makes the next song start much faster.
    if len(items) < 2:
        new_items = await _build_pool(chat_id, seed_title, seed_vidid)
        known = {i["vidid"] for i in items}
        items += [i for i in new_items if i["vidid"] not in known]
        items.sort(key=lambda x: x["score"], reverse=True)

    if not items:
        # History swallowed every candidate: reset and retry once.
        clear_history(chat_id)
        items = await _build_pool(chat_id, seed_title, seed_vidid)

    if not items:
        return None

    pick = weighted_pick(items)
    _pool[chat_id] = {
        "ts": time.time(),
        "items": [i for i in items if i["vidid"] != pick["vidid"]],
    }
    _last_auto[chat_id] = song_key(pick["title"])
    return pick

# ===========================================================
# ©️ 2026-27 All Rights Reserved by Beta Bots  😎
#
# 🧑‍💻 Developer : t.me/SUKOON_s
# 📢 Telegram channel : t.me/BETABOT_HUB
# ===========================================================
