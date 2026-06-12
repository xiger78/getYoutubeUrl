# getYoutubeUrl ユーザーマニュアル（日本語）

YouTube 検索・再生・歌詞表示・MP3/MV ダウンロード・ローカル MP3 再生を一つのウィンドウで行う GUI アプリです。YouTube API キーは不要です。

![メイン画面（日本語）](screenshots/ja.png)

---

## 目次

1. [インストールと起動](#インストールと起動)
2. [画面構成](#画面構成)
3. [言語の変更](#言語の変更)
4. [検索](#検索)
5. [再生リスト](#再生リスト)
6. [ミュージックビデオ（MV）](#ミュージックビデオmv)
7. [ローカル MP3](#ローカル-mp3)
8. [再生コントロール](#再生コントロール)
9. [歌詞パネル](#歌詞パネル)
10. [ショートカットキー](#ショートカットキー)
11. [トラブルシューティング](#トラブルシューティング)
12. [その他のコマンド](#その他のコマンド)

---

## インストールと起動

### macOS

```bash
cd getYoutubeUrl
./setup-mac.sh   # 初回のみ
./run.sh
```

### Linux（Raspberry Pi など）

```bash
cd getYoutubeUrl
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
sudo apt install -y python3-tk vlc ffmpeg
./run.sh
```

### Windows

1. `setup-windows.bat` を実行
2. `run-windows.bat` で起動

> **必要:** インターネット接続、VLC、MP3/MV 保存時は ffmpeg

---

## 画面構成

| 領域 | 説明 |
|------|------|
| 上部 | 検索種類（曲 / MV）、検索語、件数、検索 |
| 検索結果 | YouTube 検索結果一覧 |
| 検索結果ボタン | 追加、MV再生、解像度、ブラウザ、言語 |
| 再生リスト | 再生待ちの曲・MV（複数回検索で蓄積） |
| 再生リストボタン | MP3/MV ダウンロード、MIDI 生成、全体削除 |
| ローカル MP3 | PC 内フォルダの MP3 読み込み・再生 |
| 再生コントロール | 再生、削除、全体削除、ランダム、URL コピー |
| 右パネル | 歌詞 |
| 下部 | 状態メッセージ |

---

## 言語の変更

検索結果下の **「言語」** から **日本語 / 中文 / 한국어 / English** を選択します。

- **既定言語:** 日本語
- **表示順:** 日本語 → 中文 → 한국어 → English

---

## 検索

| モード | 説明 |
|--------|------|
| **🎵 曲検索** | 通常の楽曲を優先 |
| **🎬 ミュージックビデオ** | `検索語 + official mv` で MV 優先 |

1. **検索語** を入力
2. **件数**（1〜200、既定 20）を指定
3. **検索** または `Enter`

### 検索結果の操作

| ボタン / 操作 | 機能 |
|---------------|------|
| **追加 ↓** | 再生リストに追加 |
| **🎬 MV再生** | MV ポップアップで再生 |
| **解像度** | MV 再生・保存の最大解像度（HD〜4K） |
| **ブラウザで開く** | 既定ブラウザで YouTube を開く |
| **ダブルクリック** | 曲 → リスト追加 / MV → MV 再生 |

---

## 再生リスト

**追加 ↓** で曲を溜め、順番またはランダムに再生できます。

### ダウンロード・操作ボタン（左から順）

| ボタン | 機能 |
|--------|------|
| **⬇ MP3ダウンロード (全体)** | リスト全曲を MP3（192kbps）で保存 |
| **⬇ ダウンロード(MP3)** | 選択した 1 曲を MP3 で保存 |
| **⬇ MVダウンロード (全体)** | リスト内の全 MV を MP4 で保存 |
| **⬇ ダウンロード(MV)** | 選択した MV を MP4 で保存 |
| **選択曲 MIDIファイル生成** | 選択曲から KAR MIDI を生成（mido・numpy 必要） |
| **🗑 すべて削除** | **再生リストのみ** 全削除 |

リスト行 **ダブルクリック** で再生（🎵 音声 / 🎬 MV ポップアップ）。

---

## ミュージックビデオ（MV）

- 別ウィンドウ（初期 800×600）で再生
- **F11** / 映像ダブルクリックで全画面
- **Esc** で全画面解除または閉じる
- 高解像度は ffmpeg で映像+音声を結合

---

## ローカル MP3

1. **📁 フォルダ選択** で MP3 フォルダを指定（**🔄** で再スキャン）
2. サブフォルダ内の `.mp3` `.m4a` `.flac` `.ogg` `.wav` も一覧表示
3. 曲 **ダブルクリック** で再生

---

## 再生コントロール

ローカル MP3 一覧の下、**1 行** に並ぶボタン:

| ボタン | 機能 |
|--------|------|
| **▶ 再生** | 再生リスト選択 → 再生。なければローカル MP3 |
| **🗑 削除** | 再生リストまたはローカル MP3 の選択項目を削除 |
| **🗑 すべて削除** | フォーカス中: MP3 リスト / それ以外: 再生リストまたは MP3 一覧を全削除 |
| **🔀 ランダム再生** | ランダム ON にして即再生 |
| **ランダム: オフ** | ランダムモード切替 |
| **URLをすべてコピー** | 再生リスト URL をクリップボードへ |

---

## 歌詞パネル

再生開始後、右側 **歌詞** パネルに `syncedlyrics` で歌詞を表示します。

---

## ショートカットキー

| キー | 動作 |
|------|------|
| `Enter` | 検索 |
| `F11` | MV 全画面 |
| `Esc` | MV 全画面解除 / 閉じる |

---

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| 検索不可 | `pip install -U yt-dlp` |
| 再生不可 | VLC インストール確認 |
| MP3/MV 保存失敗 | ffmpeg インストール |
| ローカル MP3 が表示されない | フォルダ内に対応拡張子があるか確認、🔄 で再スキャン |
| 歌詞なし | `pip install syncedlyrics` |

**GitHub:** [https://github.com/xiger78/getYoutubeUrl](https://github.com/xiger78/getYoutubeUrl)

---

## その他のコマンド

プロジェクトルート (`getYoutubeUrl/`) で実行します。

### リポジトリの取得

```bash
git clone https://github.com/xiger78/getYoutubeUrl.git
cd getYoutubeUrl
```

### macOS

| コマンド / ファイル | 説明 |
|---------------------|------|
| `./setup-mac.sh` | uv, Python 3.11, VLC, ffmpeg, `.venv` を自動インストール |
| `./run.sh` | プログラム実行 (VLC·ffmpeg PATH 自動設定) |
| `VLC_APP=/Applications/VLC.app ./run.sh` | VLC パスを指定して実行 |
| `.venv/bin/python getYoutubeUrl.py` | 直接実行 (VLC 環境変数が必要) |

```bash
VLC_MACOS="$HOME/Applications/VLC.app/Contents/MacOS"
export DYLD_LIBRARY_PATH="$VLC_MACOS/lib"
export VLC_PLUGIN_PATH="$VLC_MACOS/plugins"
export PATH="$HOME/.local/bin:$PATH"
./.venv/bin/python getYoutubeUrl.py
```

### Linux (Debian / Raspberry Pi など)

| コマンド / ファイル | 説明 |
|---------------------|------|
| `sudo bash setup-debian.sh` | apt + `.venv` + pip 一式インストール |
| `bash setup-debian.sh --venv-only` | `.venv`·pip のみ (sudo 不要) |
| `sudo bash setup-debian.sh --with-korean` | インストール + fcitx5 韓国語入力 |
| `bash setup-debian.sh --help` | オプション一覧 |
| `./run.sh` | 実行 (`DISPLAY`, fcitx5 設定含む) |

```bash
python3 -m venv .venv
.venv/bin/pip install -U pip -r requirements.txt
sudo apt install -y python3-tk vlc ffmpeg

DISPLAY=:0 ./.venv/bin/python getYoutubeUrl.py

DISPLAY=:0 XAUTHORITY=$HOME/.Xauthority nohup ./run.sh >> /tmp/getYoutubeUrl.log 2>&1 &

pkill -f getYoutubeUrl.py
```

### Windows

| ファイル | 説明 |
|----------|------|
| `setup-windows.bat` | winget で環境構築 (なければ manual へ自動切替) |
| `setup-windows.ps1` | bat の PowerShell 本体 |
| `setup-windows-manual.bat` | winget なし手動インストール |
| `setup-windows-manual.ps1` | manual bat の PowerShell 本体 |
| `run-windows.bat` | プログラム実行 |
| `run-windows.ps1` | 実行ロジック |
| `fix-run-windows.bat` | 実行失敗時の診断·復旧 |
| `fix-run-windows.ps1` | fix bat の PowerShell 本体 |

```text
1. setup-windows.bat をダブルクリック (または setup-windows-manual.bat)
2. run-windows.bat をダブルクリック
   ※ 失敗時は fix-run-windows.bat
```

```powershell
cd getYoutubeUrl
.\run-windows.ps1
```

### マニュアル·スクリーンショット

| コマンド | 説明 |
|----------|------|
| `.venv/bin/python scripts/render_manual_screenshots.py` | 言語別 UI スクリーンショット生成 → `docs/screenshots/` |
| `./run.sh scripts/capture_manual_screenshots.py` | macOS 実ウィンドウキャプチャ (画面収録権限が必要) |

```bash
uv pip install pillow
.venv/bin/pip install pillow
```

### パッケージ更新·メンテナンス

```bash
.venv/bin/pip install -U yt-dlp
.venv/bin/pip install -U pip -r requirements.txt
.venv/bin/pip install syncedlyrics
uv pip install -r requirements.txt
```

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -U yt-dlp
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 主要ファイル

| パス | 説明 |
|------|------|
| `getYoutubeUrl.py` | 本体 |
| `i18n.py` | 多言語 UI 文字列 |
| `kar_maker.py` | KAR MIDI 生成 |
| `requirements.txt` | Python 依存関係 |
| `docs/manual_*.md` | 言語別マニュアル |
| `docs/screenshots/` | マニュアル用画像 |
| `scripts/render_manual_screenshots.py` | スクリーンショット描画 |
| `scripts/capture_manual_screenshots.py` | スクリーンショットキャプチャ |
| `README.md` | プロジェクト README |

---

## 他言語マニュアル

- [中文](manual_zh.md) · [한국어](manual_ko.md) · [English](manual_en.md)
