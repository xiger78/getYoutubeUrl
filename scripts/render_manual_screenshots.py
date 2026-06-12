#!/usr/bin/env python3
"""Render getYoutubeUrl UI screenshots for each language (for manuals)."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from i18n import LANG_MAP, LANG_OPTIONS, tr  # noqa: E402

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "-q"])
    from PIL import Image, ImageDraw, ImageFont

W, H = 1240, 900
BG = "#0f172a"
PANEL = "#111827"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
ACCENT_Y = "#fcd34d"
ACCENT_B = "#93c5fd"
ACCENT_G = "#86efac"
ACCENT_P = "#f9a8d4"
TABLE_BG = "#1e293b"
TABLE_HEAD = "#334155"
SELECT = "#38bdf8"
ENTRY_BG = "#1e293b"
LYRICS_BG = "#0b1220"

def _demo_rows(lang_code: str) -> dict:
    t = lambda k: tr(lang_code, k)  # noqa: E731
    ks, km = t("kind_song"), t("kind_mv")
    base = {
        "ja": {
            "query": "米津玄師 Lemon",
            "results": [
                ("1", km, "米津玄師 - Lemon [Official Video]", "REISSUE RECORDS", "4:15"),
                ("2", ks, "米津玄師 / Lemon", "米津玄師", "4:15"),
                ("3", km, "Lemon - 米津玄師 (Music Video)", "Sony Music", "4:15"),
            ],
            "playlist": [
                ("1", km, "▶ 米津玄師 - Lemon [Official Video]", "REISSUE RECORDS", "4:15"),
            ],
        "lyrics_title": "米津玄師 — Lemon",
        "lyrics": "夢ならばどれほど\nよかったでしょう\n未だにあなたのことを\n夢にみます\n\n忘れた物を\n取りに帰るように\n古びた記憶を\n辿るように",
            "status": "▶ 再生中: 米津玄師 - Lemon [Official Video]",
        },
        "zh": {
            "query": "周杰伦 稻香",
            "results": [
                ("1", km, "周杰伦 - 稻香 MV", "JVR Music", "3:43"),
                ("2", ks, "周杰伦 - 稻香", "周杰伦", "3:43"),
                ("3", km, "稻香 Official Music Video", "Sony Music", "3:43"),
            ],
            "playlist": [
                ("1", km, "▶ 周杰伦 - 稻香 MV", "JVR Music", "3:43"),
            ],
        "lyrics_title": "周杰伦 — 稻香",
        "lyrics": "对这个世界如果你有太多的抱怨\n跌倒了就不敢继续往前走\n为什么人要这么的脆弱 堕落\n\n请你打开电视看看\n多少人为生命在努力勇敢的走下去\n我们是不是该知足",
            "status": "▶ 正在播放: 周杰伦 - 稻香 MV",
        },
        "ko": {
            "query": "IU 좋은날",
            "results": [
                ("1", km, "IU(아이유) _ Good Day(좋은 날) MV", "1theK", "3:53"),
                ("2", ks, "IU - 좋은날", "IU Official", "3:53"),
                ("3", km, "Good Day Official MV", "LOEN", "3:53"),
            ],
            "playlist": [
                ("1", km, "▶ IU(아이유) _ Good Day(좋은 날) MV", "1theK", "3:53"),
            ],
        "lyrics_title": "IU — 좋은날",
        "lyrics": "이러다 미쳐버릴 것 같아\n너무 좋은 날\n\n너와 나\n둘이서\n\n하늘을 날아\n구름 위를\n\n좋은 날",
            "status": "▶ 재생 중: IU(아이유) _ Good Day(좋은 날) MV",
        },
        "en": {
            "query": "Ed Sheeran Shape of You",
            "results": [
                ("1", km, "Ed Sheeran - Shape of You [Official Video]", "Ed Sheeran", "4:23"),
                ("2", ks, "Ed Sheeran - Shape of You", "Ed Sheeran", "3:53"),
                ("3", km, "Shape of You (Official Music Video)", "Warner", "4:23"),
            ],
            "playlist": [
                ("1", km, "▶ Ed Sheeran - Shape of You [Official Video]", "Ed Sheeran", "4:23"),
            ],
        "lyrics_title": "Ed Sheeran — Shape of You",
        "lyrics": "The club isn't the best place to find a lover\nSo the bar is where I go\nMe and my friends at the table doing shots\n\nDrinking fast and then we talk slow\nCome over and start up a conversation with just me",
            "status": "▶ Playing: Ed Sheeran - Shape of You [Official Video]",
        },
    }
    return base[lang_code]


def _fonts() -> tuple[ImageFont.FreeTypeFont, ...]:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    path = next((p for p in candidates if os.path.isfile(p)), None)
    if path:
        return (
            ImageFont.truetype(path, 11),
            ImageFont.truetype(path, 10),
            ImageFont.truetype(path, 12),
            ImageFont.truetype(path, 10, index=0),
            ImageFont.truetype(path, 9),
        )
    d = ImageFont.load_default()
    return d, d, d, d, d


def _btn(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, font, w: int | None = None) -> int:
    tw = draw.textlength(text, font=font)
    bw = int(tw + 20) if w is None else w
    draw.rounded_rectangle((x, y, x + bw, y + 28), radius=4, fill=TABLE_HEAD, outline="#475569")
    draw.text((x + 10, y + 6), text, fill=TEXT, font=font)
    return bw


def _table(
    draw: ImageDraw.ImageDraw,
    x: int, y: int, w: int, h: int,
    headers: list[str], rows: list[tuple[str, ...]],
    font, font_sm, sel_row: int | None = None,
) -> None:
    draw.rectangle((x, y, x + w, y + h), fill=TABLE_BG)
    cols = [36, 72, w - 36 - 72 - 150 - 64 - 8, 150, 64]
    cx = x
    for i, hdr in enumerate(headers):
        draw.rectangle((cx, y, cx + cols[i], y + 26), fill=TABLE_HEAD)
        draw.text((cx + 6, y + 5), hdr, fill="#f8fafc", font=font_sm)
        cx += cols[i]
    ry = y + 26
    for ri, row in enumerate(rows):
        bg = SELECT if sel_row == ri else TABLE_BG
        fg = "#0f172a" if sel_row == ri else TEXT
        cx = x
        for ci, cell in enumerate(row):
            draw.rectangle((cx, ry, cx + cols[ci], ry + 26), fill=bg)
            draw.text((cx + 6, ry + 5), cell[:42], fill=fg, font=font_sm)
            cx += cols[ci]
        ry += 26


def render(lang_code: str, out_path: str) -> None:
    t = lambda k, **kw: tr(lang_code, k, **kw)  # noqa: E731
    demo = _demo_rows(lang_code)
    lang_display = next(k for k, v in LANG_MAP.items() if v == lang_code)

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    f_bold, f_norm, f_title, _, f_sm = _fonts()

    # Title bar
    draw.rectangle((0, 0, W, 28), fill="#1e293b")
    draw.text((12, 6), t("window_title"), fill=TEXT, font=f_norm)

    left_w = W - 320
    rx = left_w

    # Lyrics panel
    draw.rectangle((rx, 28, W, H - 28), fill=PANEL)
    draw.text((rx + 12, 40), t("lyrics"), fill=ACCENT_Y, font=f_bold)
    draw.text((rx + 12, 62), demo["lyrics_title"], fill="#cbd5e1", font=f_sm)
    draw.rectangle((rx + 12, 88, W - 12, H - 36), fill=LYRICS_BG)
    ly = 98
    for line in demo["lyrics"].split("\n"):
        draw.text((rx + 20, ly), line, fill=TEXT, font=f_norm)
        ly += 18

    # Search kind
    y = 42
    draw.text((16, y), t("search_kind"), fill=ACCENT_Y, font=f_bold)
    draw.text((100, y), f"● {t('song_mode')}", fill=TEXT, font=f_norm)
    draw.text((220, y), f"○ {t('mv_mode')}", fill=MUTED, font=f_norm)

    # Query row
    y = 72
    draw.text((16, y + 4), t("query"), fill=TEXT, font=f_bold)
    draw.rectangle((70, y, left_w - 200, y + 32), fill=ENTRY_BG)
    draw.text((80, y + 8), demo["query"], fill=TEXT, font=f_title)
    draw.text((left_w - 190, y + 8), t("count"), fill="#cbd5e1", font=f_norm)
    draw.rectangle((left_w - 150, y + 4, left_w - 110, y + 28), fill=ENTRY_BG, outline="#475569")
    draw.text((left_w - 142, y + 8), "20", fill=TEXT, font=f_norm)
    _btn(draw, left_w - 100, y + 2, t("search"), f_norm, 70)

    # Search results
    y = 118
    draw.text((16, y), t("search_results"), fill=ACCENT_B, font=f_bold)
    y += 22
    headers = [t("col_no"), t("col_kind"), t("col_title"), t("col_channel"), t("col_dur")]
    _table(draw, 16, y, left_w - 32, 26 + 26 * 3, headers, demo["results"], f_norm, f_sm)

    # Result buttons (no delete)
    y += 26 + 26 * 3 + 8
    bx = 16
    for key in ("add", "mv_play"):
        bx += _btn(draw, bx, y, t(key), f_sm) + 6
    draw.text((bx + 8, y + 6), t("resolution"), fill="#cbd5e1", font=f_sm)
    draw.rectangle((bx + 58, y + 2, bx + 108, y + 26), fill=ENTRY_BG, outline="#475569")
    draw.text((bx + 68, y + 6), "FHD", fill=TEXT, font=f_sm)
    bx += 118
    bx += _btn(draw, bx, y, t("browser"), f_sm) + 6
    draw.text((bx + 8, y + 6), t("language"), fill="#cbd5e1", font=f_sm)
    draw.rectangle((bx + 58, y + 2, bx + 138, y + 26), fill=ENTRY_BG, outline="#475569")
    draw.text((bx + 68, y + 6), lang_display, fill=TEXT, font=f_sm)

    # Playlist
    y += 40
    draw.text((16, y), t("playlist"), fill=ACCENT_G, font=f_bold)
    y += 22
    _table(draw, 16, y, left_w - 32, 26 + 26, headers, demo["playlist"], f_norm, f_sm, sel_row=0)

    # Playlist download / clear buttons
    y += 26 + 26 + 8
    bx = 16
    for key in (
        "save_mp3_all", "save_mp3_sel", "save_mv_all",
        "save_mv_sel", "kar_create", "clear_pl_list",
    ):
        bx += _btn(draw, bx, y, t(key), f_sm) + 3

    # Local MP3
    y += 36
    draw.text((16, y), t("local_mp3"), fill=ACCENT_P, font=f_bold)
    draw.text((120, y + 1), t("folder_unset"), fill=MUTED, font=f_sm)
    _btn(draw, left_w - 120, y - 2, t("pick_folder"), f_sm)

    y += 24
    mp3_headers = [t("col_no"), t("col_filename"), t("col_dur")]
    draw.rectangle((16, y, left_w - 16, y + 52), fill=TABLE_BG)
    cx = 16
    for i, hdr in enumerate(mp3_headers):
        cw = [36, left_w - 16 - 36 - 64 - 16, 64][i]
        draw.rectangle((cx, y, cx + cw, y + 26), fill=TABLE_HEAD)
        draw.text((cx + 6, y + 5), hdr, fill="#f8fafc", font=f_sm)
        cx += cw

    # Playback controls (single row)
    y += 62
    bx = 16
    for key in ("play", "delete", "clear_pl", "shuffle"):
        bx += _btn(draw, bx, y, t(key), f_sm) + 3
    _btn(draw, bx, y, t("shuffle_off"), f_sm, 90)
    bx += 96
    _btn(draw, bx, y, t("copy_urls"), f_sm)

    # Status bar
    draw.rectangle((0, H - 24, W, H), fill=BG)
    draw.text((16, H - 20), demo["status"], fill=MUTED, font=f_sm)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, optimize=True)
    print(out_path, os.path.getsize(out_path))


def main() -> None:
    out_dir = os.path.join(ROOT, "docs", "screenshots")
    for display in LANG_OPTIONS:
        render(LANG_MAP[display], os.path.join(out_dir, f"{LANG_MAP[display]}.png"))


if __name__ == "__main__":
    main()
