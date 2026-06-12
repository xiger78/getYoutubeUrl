# getYoutubeUrl Documentation

User manuals with UI screenshots for each supported language.

| Language | Manual | Screenshot |
|----------|--------|------------|
| 日本語 (default) | [manual_ja.md](manual_ja.md) | [screenshots/ja.png](screenshots/ja.png) |
| 中文 | [manual_zh.md](manual_zh.md) | [screenshots/zh.png](screenshots/zh.png) |
| 한국어 | [manual_ko.md](manual_ko.md) | [screenshots/ko.png](screenshots/ko.png) |
| English | [manual_en.md](manual_en.md) | [screenshots/en.png](screenshots/en.png) |

Language order in app: **日本語 → 中文 → 한국어 → English**

## Regenerate screenshots

```bash
.venv/bin/python scripts/render_manual_screenshots.py
```

Screenshots reflect the current UI layout (playlist download buttons, local MP3, single-row playback controls).

Live capture (macOS, Screen Recording permission):

```bash
./run.sh scripts/capture_manual_screenshots.py
```
