"""
MP3 → 가라오케 KAR MIDI 변환.

- ffmpeg 로 WAV 추출
- numpy 자기상관 기반 멜로디 추출 → MIDI 음표
- syncedlyrics LRC 가사 → KAR 텍스트 이벤트
"""

from __future__ import annotations

import re
import struct
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo

try:
    import syncedlyrics

    _HAS_LYRICS = True
except ImportError:
    _HAS_LYRICS = False

TICKS_PER_BEAT = 480
DEFAULT_BPM = 120
LRC_LINE_RE = re.compile(
    r"\[(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?\]\s*(.*)"
)


def _run_ffmpeg(args: list[str]) -> None:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", *args],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "ffmpeg failed").strip()
        raise RuntimeError(err)


def mp3_to_wav(mp3_path: str | Path, wav_path: str | Path) -> None:
    _run_ffmpeg([
        "-y", "-i", str(mp3_path),
        "-ac", "1", "-ar", "22050",
        str(wav_path),
    ])


def _read_wav(path: str | Path) -> tuple[np.ndarray, int]:
    data = Path(path).read_bytes()
    if len(data) < 44 or data[:4] != b"RIFF":
        raise RuntimeError("WAV 파일을 읽지 못했습니다.")
    channels = struct.unpack_from("<H", data, 22)[0]
    sample_rate = struct.unpack_from("<I", data, 24)[0]
    bits = struct.unpack_from("<H", data, 34)[0]
    audio = data[44:]
    if bits == 16:
        samples = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
    elif bits == 32:
        samples = np.frombuffer(audio, dtype=np.float32)
    else:
        raise RuntimeError(f"지원하지 않는 WAV 비트 깊이: {bits}")
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)
    return samples, sample_rate


def _freq_to_midi(freq: float) -> int | None:
    if freq <= 0:
        return None
    midi = int(round(69 + 12 * np.log2(freq / 440.0)))
    if 36 <= midi <= 96:
        return midi
    return None


def _frame_pitch(frame: np.ndarray, sr: int) -> float | None:
    if len(frame) < 512:
        return None
    frame = frame * np.hanning(len(frame))
    corr = np.correlate(frame, frame, mode="full")
    corr = corr[len(corr) // 2 :]
    min_lag = int(sr / 900)
    max_lag = int(sr / 65)
    if max_lag >= len(corr):
        return None
    segment = corr[min_lag:max_lag]
    if segment.size == 0:
        return None
    peak = int(np.argmax(segment)) + min_lag
    if corr[peak] < corr[0] * 0.3:
        return None
    return sr / peak


def extract_melody_notes(
    wav_path: str | Path,
    hop_sec: float = 0.08,
    min_note_sec: float = 0.12,
) -> list[tuple[float, float, int, int]]:
    """(시작초, 끝초, MIDI노트, velocity) 목록."""
    samples, sr = _read_wav(wav_path)
    hop = max(256, int(sr * hop_sec))
    frame_len = hop * 2
    notes: list[tuple[float, float, int, int]] = []
    cur_note: int | None = None
    cur_start = 0.0
    last_time = 0.0

    for i in range(0, len(samples) - frame_len, hop):
        t = i / sr
        frame = samples[i : i + frame_len]
        rms = float(np.sqrt(np.mean(frame * frame)))
        if rms < 0.015:
            midi = None
        else:
            freq = _frame_pitch(frame, sr)
            midi = _freq_to_midi(freq) if freq else None

        if midi != cur_note:
            if cur_note is not None and (t - cur_start) >= min_note_sec:
                notes.append((cur_start, t, cur_note, 80))
            cur_note = midi
            cur_start = t
        last_time = t + hop / sr

    if cur_note is not None and (last_time - cur_start) >= min_note_sec:
        notes.append((cur_start, last_time, cur_note, 80))
    return notes


def _lrc_seconds(m: re.Match[str]) -> float:
    mm, ss, frac, _ = m.groups()
    sec = int(mm) * 60 + int(ss)
    if frac:
        sec += int(frac.ljust(3, "0")[:3]) / 1000.0
    return sec


def parse_lrc(lrc_text: str) -> list[tuple[float, str]]:
    events: list[tuple[float, str]] = []
    for line in lrc_text.splitlines():
        m = LRC_LINE_RE.match(line.strip())
        if not m:
            continue
        text = m.group(4).strip()
        if text:
            events.append((_lrc_seconds(m), text))
    events.sort(key=lambda x: x[0])
    return events


def fetch_synced_lyrics(title: str) -> list[tuple[float, str]]:
    if not _HAS_LYRICS or not title.strip():
        return []
    try:
        lrc = syncedlyrics.search(title, synced_only=True)
    except Exception:  # noqa: BLE001
        lrc = None
    if not lrc:
        try:
            lrc = syncedlyrics.search(title)
        except Exception:  # noqa: BLE001
            lrc = None
    if not lrc:
        return []
    return parse_lrc(lrc)


def _sec_to_delta(sec: float, tempo: int, prev_sec: float) -> int:
    delta_us = int(max(0.0, sec - prev_sec) * 1_000_000)
    return int(delta_us * TICKS_PER_BEAT / tempo)


def _split_kar_line(text: str) -> list[str]:
    """KAR 형식: 첫 줄 \\, 이후 줄은 / 접두."""
    words = text.split()
    if not words:
        return []
    parts = [f"\\{words[0]}"]
    for w in words[1:]:
        parts.append(f"/{w}")
    return parts


def build_kar(
    notes: list[tuple[float, float, int, int]],
    lyrics: list[tuple[float, str]],
    title: str,
    artist: str = "",
    bpm: int = DEFAULT_BPM,
) -> MidiFile:
    mid = MidiFile(type=1, ticks_per_beat=TICKS_PER_BEAT)
    tempo = bpm2tempo(bpm)

    # 트랙 0: KAR 식별 + 템포
    hdr = MidiTrack()
    hdr.append(MetaMessage("text", text="@KMIDI KARAOKE FILE", time=0))
    hdr.append(MetaMessage("text", text="@V0100", time=0))
    hdr.append(MetaMessage("set_tempo", tempo=tempo, time=0))
    hdr.append(MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    hdr.append(MetaMessage("end_of_track", time=0))
    mid.tracks.append(hdr)

    # 트랙 1: 가사
    lyr = MidiTrack()
    lang = "@LKOR" if _has_hangul(title) else "@LENGL"
    lyr.append(MetaMessage("text", text=lang, time=0))
    lyr.append(MetaMessage("text", text=f"@T{title}", time=0))
    if artist:
        lyr.append(MetaMessage("text", text=f"@T{artist}", time=0))

    prev = 0.0
    for ts, line in lyrics:
        for chunk in _split_kar_line(line):
            lyr.append(MetaMessage("text", text=chunk, time=_sec_to_delta(ts, tempo, prev)))
            prev = ts
    lyr.append(MetaMessage("end_of_track", time=0))
    mid.tracks.append(lyr)

    # 트랙 2: 멜로디
    melody = MidiTrack()
    melody.append(MetaMessage("track_name", name="Melody", time=0))
    prev = 0.0
    for start, end, note, vel in notes:
        melody.append(Message(
            "note_on", note=note, velocity=vel, time=_sec_to_delta(start, tempo, prev),
        ))
        prev = start
        melody.append(Message(
            "note_off", note=note, velocity=0, time=_sec_to_delta(end, tempo, prev),
        ))
        prev = end
    melody.append(MetaMessage("end_of_track", time=0))
    mid.tracks.append(melody)

    return mid


def _has_hangul(text: str) -> bool:
    return bool(re.search(r"[\uac00-\ud7a3]", text))


def _safe_stem(path: str | Path) -> str:
    return Path(path).stem


def create_kar_from_mp3(
    mp3_path: str | Path,
    output_path: str | Path | None = None,
    title: str | None = None,
    artist: str = "",
) -> Path:
    mp3_path = Path(mp3_path)
    if not mp3_path.is_file():
        raise FileNotFoundError(f"MP3 파일 없음: {mp3_path}")

    song_title = (title or _safe_stem(mp3_path)).strip()
    out = Path(output_path) if output_path else mp3_path.with_suffix(".kar")
    if out.suffix.lower() != ".kar":
        out = out.with_suffix(".kar")

    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "audio.wav"
        mp3_to_wav(mp3_path, wav)
        notes = extract_melody_notes(wav)
        if not notes:
            raise RuntimeError("멜로디를 추출하지 못했습니다. (볼륨이 너무 작거나 단순 반주일 수 있음)")

        lyrics = fetch_synced_lyrics(song_title)
        mid = build_kar(notes, lyrics, song_title, artist=artist)
        out.parent.mkdir(parents=True, exist_ok=True)
        mid.save(str(out))

    return out
