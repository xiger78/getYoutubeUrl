# getYoutubeUrl Documentation

User manuals and screenshots for each supported UI language.

| Language | Manual | Screenshot |
|----------|--------|------------|
| 日本語 (default) | [manual_ja.md](manual_ja.md) | [screenshots/ja.png](screenshots/ja.png) |
| 中文 | [manual_zh.md](manual_zh.md) | [screenshots/zh.png](screenshots/zh.png) |
| 한국어 | [manual_ko.md](manual_ko.md) | [screenshots/ko.png](screenshots/ko.png) |
| English | [manual_en.md](manual_en.md) | [screenshots/en.png](screenshots/en.png) |

Language selector order in the app: **日本語 → 中文 → 한국어 → English**

## Regenerate screenshots

```bash
# Render UI mock screenshots (works everywhere)
.venv/bin/python scripts/render_manual_screenshots.py

# Live window capture (macOS, Screen Recording permission required)
./run.sh scripts/capture_manual_screenshots.py
```

If live capture fails or produces oversized files, use the render script above.
