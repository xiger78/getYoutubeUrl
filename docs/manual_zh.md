# getYoutubeUrl — YouTube 搜索 · 播放 · MP3 保存

基于 Python3 + tkinter + yt-dlp + libVLC 的 GUI 程序。  
按歌名搜索 YouTube，加入**播放列表**后可在同一窗口内**播放**、**显示歌词**、**下载 MP3/MV**、**播放本地 MP3**、**生成 KAR MIDI**。  
可选**歌曲搜索**与**音乐视频搜索**；MV 在 **800×600 弹窗**中按所选分辨率（HD~4K）播放。  
（无需 YouTube API 密钥 · **默认 UI 语言：日语**）

![主界面（中文）](screenshots/zh.png)

---

## 目录

- [主要功能](#主要功能)
- [开发环境](#开发环境)
- [依赖包](#依赖包)
- [安装与运行](#安装与运行)
- [切换语言](#切换语言)
- [界面与按钮](#界面与按钮)
- [快捷键](#快捷键)
- [项目结构](#项目结构)
- [工作原理](#工作原理)
- [变更历史](#变更历史)
- [故障排除](#故障排除)
- [其他命令](#其他命令)
- [其他语言手册](#其他语言手册)

---

## 主要功能

- **🎵 歌曲搜索** / **🎬 音乐视频** 搜索模式（默认 20 条，最多 200 条）
- 搜索结果·播放列表显示**类型**（`🎵 歌曲` / `🎬 MV` / `💾 本地`）
- 搜索结果 **双击立即播放**（歌曲·MV，不加入播放列表）
- 搜索结果**无限累积**到播放列表（**添加 ↓** 按钮，防 URL 重复）
- **歌曲**：主窗口 libVLC 音频流播放
- **MV**：独立**弹窗**（初始 800×600）HD~4K 播放，F11 全屏
- 右侧面板**歌词**显示（syncedlyrics）
- 播放列表 **MP3（192kbps）批量·选中保存**
- 播放列表 **MV MP4 批量·选中保存**（可选分辨率）
- 从 **MP3 保存文件夹内全部歌曲** 批量生成 **KAR MIDI**
- **本地 MP3 文件夹** 加载·播放（含子文件夹）
- **UI 多语言**：日本語 · 中文 · 한국어 · English
- **随机播放**、曲目结束后自动下一首
- **Linux / macOS / Windows** 安装·运行脚本
- 搜索·播放·歌词·下载·MV 加载均在**后台线程**（防止 GUI 冻结）

---

## 开发环境

### Raspberry Pi（主要开发·测试环境）

| 项目 | 内容 |
|------|------|
| 设备 | Raspberry Pi (aarch64 / arm64) |
| OS | Debian GNU/Linux 13 (trixie) |
| 桌面 | Wayland (labwc) + XWayland |
| Python | 3.13.5 |
| GUI | tkinter (`python3-tk`) |
| 媒体 | libVLC 3.0.23 "Vetinari" |
| 虚拟环境 | `.venv/` |
| 初始窗口 | 1240×900（最小 1000×780） |

> tkinter 使用 XWayland 显示（`:0`）。`run.sh` 自动设置 `DISPLAY`·`XAUTHORITY`。

### macOS / Windows

| OS | Python | VLC | ffmpeg | 安装 |
|----|--------|-----|--------|------|
| macOS | uv + Python 3.11 | `~/Applications/VLC.app` | `~/.local/bin/ffmpeg` | `setup-mac.sh` |
| Windows | Python 3.12 | VideoLAN VLC | `%LOCALAPPDATA%\getYoutubeUrl\bin` | `setup-windows.bat` 等 |

---

## 依赖包

### 系统包（apt 示例）

| 包 | 用途 |
|----|------|
| `python3` | 运行时 |
| `python3-tk` | tkinter GUI |
| `libvlc5` / `vlc-bin` | libVLC 播放 |
| `ffmpeg` | MP3/MV 转换·合并 |

### Python 包（`.venv`）

| 包 | 用途 |
|----|------|
| `yt-dlp` | YouTube 搜索·流·下载 |
| `python-vlc` | libVLC Python 绑定 |
| `syncedlyrics` | 歌词搜索 |
| `mido` · `numpy` | KAR MIDI 生成（可选） |

> 无 `syncedlyrics` 时除歌词外均可使用。无 `mido`·`numpy` 时 KAR 按钮会显示错误。

---

## 安装与运行

### Linux（Raspberry Pi 等）

```bash
cd getYoutubeUrl
sudo bash setup-debian.sh          # 推荐（apt + .venv）
# 或
python3 -m venv .venv
.venv/bin/pip install -U pip -r requirements.txt
sudo apt install -y python3-tk vlc ffmpeg

./run.sh
```

直接运行:

```bash
DISPLAY=:0 ./.venv/bin/python getYoutubeUrl.py
```

后台（SSH 等）:

```bash
DISPLAY=:0 XAUTHORITY=$HOME/.Xauthority nohup ./run.sh >> /tmp/getYoutubeUrl.log 2>&1 &
pkill -f getYoutubeUrl.py   # 退出
```

### macOS

```bash
cd getYoutubeUrl
./setup-mac.sh
./run.sh
```

### Windows

| 脚本 | 用途 |
|------|------|
| `setup-windows.bat` | winget 搭建（无则自动转 manual） |
| `setup-windows-manual.bat` | 手动安装 |
| `run-windows.bat` | 运行 |
| `fix-run-windows.bat` | 运行失败时诊断·修复 |

```text
1. 双击 setup-windows.bat
2. 双击 run-windows.bat
```

> `.bat` 为 ASCII + CRLF。实际逻辑由 `.ps1` 执行。需要网络连接。

---

## 切换语言

在搜索结果下方的 **「语言」** 下拉框中选择:

**日本語 → 中文 → 한국어 → English**（默认：**日语**）

---

## 界面与按钮

左侧（搜索·列表·操作）+ 右侧（歌词 320px）。底部为**状态栏**。

### 顶部 — 搜索

| UI | 功能 |
|----|------|
| **🎵 歌曲搜索** | 优先普通歌曲（MV 标题靠后） |
| **🎬 音乐视频** | `搜索词 + official mv`，优先 MV |
| **搜索词** | 歌名·艺术家 |
| **数量** | 1~200（默认 20） |
| **搜索** | 后台搜索（同 `Enter`） |

### 搜索结果

| 列 | 说明 |
|----|------|
| # · 类型 · 标题 · 频道 · 时长 | |

| 按钮 / 操作 | 功能 |
|-------------|------|
| **添加 ↓** | 加入播放列表（跳过重复 URL）。**仅通过此按钮添加列表** |
| **🎬 MV播放** | 在弹窗中播放所选 MV |
| **分辨率** | MV 播放·保存最大分辨率（HD / FHD / QHD / 2K / 4K） |
| **在浏览器中打开** | 默认浏览器打开 YouTube |
| **语言** | 切换 UI 语言 |
| **双击** | **立即播放**所选项（歌曲·MV）。不加入播放列表 |

### 播放列表

| 列 | 说明 |
|----|------|
| # · 类型 · 标题 · 频道 · 时长 | `▶` = 正在播放 |

| 按钮（从左到右） | 功能 |
|------------------|------|
| **⬇ MP3 下载 (全部)** | 整列表保存 MP3（192kbps） |
| **⬇ 下载(MP3)** | 保存选中 1 首 MP3 |
| **⬇ MV 下载 (全部)** | 列表内全部 MV 保存 MP4 |
| **⬇ 下载(MV)** | 保存选中 MV 为 MP4 |
| **全部歌曲生成 MIDI** | 从 **MP3 保存时指定的文件夹** 内全部 `.mp3` 生成 `.kar` |
| **🗑 全部删除** | **仅清空播放列表** |

保存时选择文件夹。状态栏显示进度。**ffmpeg** 必需（MP3·MV·KAR 共用）。

**双击**：歌曲 → 音频播放 / MV → 弹窗。

### 本地 MP3

| UI | 功能 |
|----|------|
| **📁 选择文件夹** | 指定 PC 内 MP3 文件夹 |
| **🔄** | 重新扫描 |
| 列表 | `.mp3` `.m4a` `.flac` `.ogg` `.wav`（含子文件夹） |
| **双击** | 播放本地 MP3 |

### 播放控制（单行）

| 按钮 | 功能 |
|------|------|
| **▶ 播放** | 播放列表选中 → 否则本地 MP3 |
| **🗑 删除** | 从列表或 MP3 列表删除选中项 |
| **🗑 全部删除** | 按焦点清空 MP3 列表或播放列表 |
| **🔀 随机播放** | 开启随机并立即播放 |
| **随机: 关/开** | 切换下一首·自动下一首的随机模式 |
| **复制全部 URL** | 复制播放列表 URL 到剪贴板 |

### 右侧 — 歌词面板

播放中歌曲的歌词由 `syncedlyrics` 显示（可滚动）。

### MV 弹窗

| 项目 | 内容 |
|------|------|
| 初始大小 | 800×600（最小 640×480） |
| 分辨率 | 搜索结果旁的 **分辨率** 选择（ffmpeg 合并音视频） |
| **F11** / 视频双击 | 全屏 |
| **Esc** | 退出全屏或关闭 |
| 自动 | MV 播放时主窗口音频停止 |

---

## 快捷键

| 键 | 动作 | 对象 |
|----|------|------|
| `Enter` | 搜索 | 主窗口 |
| `F11` | 全屏 | MV 弹窗 |
| `Esc` | 退出全屏 / 关闭 | MV 弹窗 |

---

## 项目结构

| 文件 / 文件夹 | 说明 |
|---------------|------|
| `getYoutubeUrl.py` | 主程序（tkinter GUI） |
| `i18n.py` | UI 多语言字符串 |
| `kar_maker.py` | MP3 → KAR MIDI 转换 |
| `requirements.txt` | Python 依赖 |
| `run.sh` | Linux/macOS 运行 |
| `setup-mac.sh` | macOS 环境搭建 |
| `setup-debian.sh` | Debian/树莓派环境搭建 |
| `setup-windows*.bat/ps1` | Windows 环境搭建 |
| `run-windows*.bat/ps1` | Windows 运行 |
| `fix-run-windows*.bat/ps1` | Windows 运行修复 |
| `docs/manual_*.md` | 各语言用户手册 |
| `docs/screenshots/` | 手册截图 |
| `scripts/render_manual_screenshots.py` | 截图渲染 |
| `scripts/capture_manual_screenshots.py` | 截图捕获 |
| `.venv/` | 虚拟环境 |

---

## 工作原理

### 搜索

- **歌曲模式：** `ytsearch{N}:搜索词` — 排除 MV 标题优先
- **MV 模式：** `ytsearch{N}:搜索词 official mv` — MV 优先
- `extract_flat` 仅获取元数据

### 搜索结果的播放与添加

- **双击**：不加入播放列表，直接播放（歌曲在主窗口，MV 在弹窗）
- **添加 ↓**：仅加入播放列表（不播放）

### 播放列表

- 内存 `list[dict]`，曲数不限，防 URL 重复

### 播放（歌曲）

1. `yt-dlp` 获取音频 URL
2. libVLC 流播放

### 播放（MV）

1. `MvPlayerWindow` 弹窗
2. 所选分辨率以下 yt-dlp + ffmpeg 合并
3. VLC 嵌入 `video_panel`

### 歌词

- 后台执行 `syncedlyrics.search()`

### MP3 保存

- yt-dlp + FFmpegExtractAudio → mp3 192kbps
- 保存文件夹亦用于 **全部歌曲生成 MIDI**

### MV 保存

- 仅播放列表中 `media_type == "mv"`
- 所选分辨率以下 MP4

### KAR MIDI

- 将 MP3 下载指定文件夹内 `.mp3` 依次转为 `.kar`（输出到同文件夹）

### 随机播放

- `shuffle=True` 时下一首·曲目结束自动切换为随机

---

## 变更历史

| 版本 | 内容 |
|------|------|
| v1 | YouTube 搜索前 10 + URL 显示 |
| v2 | 播放列表·VLC 流播放 |
| v3 | 多次搜索累积·随机·删除 |
| v4 | 歌词面板 |
| v5 | MP3 批量保存 |
| v6 | 搜索数量 1~200·选中 MP3 保存 |
| v7 | 窗口 1240×820 |
| v8 | 歌曲/MV 搜索区分·MV 弹窗 |
| v9 | MV 800×600·Full HD·F11/Esc |
| v10 | Windows 脚本 |
| v11 | Windows manual·fix-run |
| v12 | MV MP4 批量·选中保存 |
| v13 | Windows bat/ps1 分离 |
| v14 | UI 多语言(ja/zh/ko/en)·分辨率选择·本地 MP3 |
| v15 | MP3 保存文件夹全曲 KAR MIDI·UI 按钮整理 |
| v16 | 搜索结果双击即播放，加入列表仅用 **添加 ↓** 按钮 |

---

## 故障排除

- **GitHub:** [https://github.com/xiger78/getYoutubeUrl](https://github.com/xiger78/getYoutubeUrl)
- 因地区·YouTube 政策，部分视频可能失败
- 无法搜索 → `.venv/bin/pip install -U yt-dlp`
- 无法播放 → 检查 VLC 安装
- MP3/MV/KAR 失败 → 检查 **ffmpeg**
- KAR 不可用 → `pip install mido numpy`
- 无歌词 → `pip install syncedlyrics`
- 本地 MP3 不显示 → 检查扩展名·🔄 重新扫描
- Windows 安装 → `setup-windows.bat` 或 `setup-windows-manual.bat`
- Windows 运行 → `fix-run-windows.bat`
- Linux 韩文输入 → `setup-debian.sh --with-korean`（fcitx5）

---

## 其他命令

在项目根目录执行。

### 仓库

```bash
git clone https://github.com/xiger78/getYoutubeUrl.git
cd getYoutubeUrl
```

### macOS

```bash
./setup-mac.sh
./run.sh
VLC_APP=/Applications/VLC.app ./run.sh
```

### Linux

```bash
sudo bash setup-debian.sh
sudo bash setup-debian.sh --with-korean
bash setup-debian.sh --venv-only
./run.sh
pkill -f getYoutubeUrl.py
```

### Windows

```powershell
.\run-windows.ps1
```

### 手册截图

```bash
.venv/bin/python scripts/render_manual_screenshots.py
./run.sh scripts/capture_manual_screenshots.py   # macOS·屏幕录制权限
```

### 包更新

```bash
.venv/bin/pip install -U yt-dlp
.venv/bin/pip install -U pip -r requirements.txt
uv pip install -r requirements.txt
```

---

## 其他语言手册

- [日本語](manual_ja.md) · [한국어](manual_ko.md) · [English](manual_en.md)
