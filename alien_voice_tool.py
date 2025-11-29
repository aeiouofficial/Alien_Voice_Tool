"""Command line tool to morph a vocal track into an "alien" texture.

Usage:
    python alien_voice_tool.py input_audio.[wav|mp3] --output output.wav

MP3 decoding uses pydub+ffmpeg when available. Otherwise convert to WAV first.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Tuple

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

try:  # Optional dependency for MP3 and non-WAV inputs
    from pydub import AudioSegment
except ImportError:  # pragma: no cover - optional
    AudioSegment = None  # type: ignore


def butter_lowpass(cutoff_hz: float, sample_rate: int, order: int = 6) -> Tuple[np.ndarray, np.ndarray]:
    nyquist = 0.5 * sample_rate
    if cutoff_hz >= nyquist:
        raise ValueError("Low-pass cutoff must be below Nyquist frequency")
    normal_cutoff = cutoff_hz / nyquist
    return butter(order, normal_cutoff, btype="low", analog=False)


def ensure_float32(data: np.ndarray) -> np.ndarray:
    if np.issubdtype(data.dtype, np.floating):
        return data.astype(np.float32, copy=False)
    max_val = np.iinfo(data.dtype).max
    return (data.astype(np.float32) / max_val).clip(-1.0, 1.0)


def load_audio(path: Path) -> Tuple[int, np.ndarray]:
    ext = path.suffix.lower()
    if ext == ".wav":
        sample_rate, raw = wavfile.read(path)
        return sample_rate, ensure_float32(raw)
    if AudioSegment is None:
        raise RuntimeError(
            "Non-WAV input detected. Install pydub and ffmpeg or convert to WAV manually."
        )
    segment = AudioSegment.from_file(path)
    sample_rate = segment.frame_rate
    samples = np.array(segment.get_array_of_samples(), dtype=np.float32)
    if segment.channels > 1:
        samples = samples.reshape((-1, segment.channels)).mean(axis=1)
    max_val = float(1 << (8 * segment.sample_width - 1))
    samples /= max_val
    return sample_rate, samples


def write_audio(path: Path, sample_rate: int, data: np.ndarray) -> None:
    clipped = np.clip(data, -1.0, 1.0)
    wavfile.write(path, sample_rate, (clipped * 32767).astype(np.int16))


def granular_stutter(
    signal: np.ndarray,
    sample_rate: int,
    grain_ms: float,
    drop_prob: float,
    pitch_prob: float,
    pitch_step: int,
    seed: int | None,
) -> np.ndarray:
    grain_len = max(1, int(sample_rate * (grain_ms / 1000.0)))
    rng = np.random.default_rng(seed)
    grains = []
    for start in range(0, len(signal), grain_len):
        grain = signal[start : start + grain_len]
        if len(grain) == 0:
            continue
        if rng.random() < drop_prob:
            grains.append(np.zeros_like(grain))
            continue
        if rng.random() < pitch_prob and len(grain) > 1:
            grain = grain[::pitch_step]
        grains.append(grain)
    if not grains:
        return signal.copy()
    return np.concatenate(grains)


def ring_mod(signal: np.ndarray, sample_rate: int, freq_hz: float) -> np.ndarray:
    t = np.arange(len(signal)) / float(sample_rate)
    modulator = np.sin(2 * np.pi * freq_hz * t)
    return signal * modulator


def hard_clip(signal: np.ndarray, drive: float) -> np.ndarray:
    return np.clip(signal * drive, -1.0, 1.0)


def apply_lowpass(signal: np.ndarray, sample_rate: int, cutoff_hz: float) -> np.ndarray:
    b, a = butter_lowpass(cutoff_hz, sample_rate)
    return lfilter(b, a, signal)


def match_length(signal: np.ndarray, target_len: int) -> np.ndarray:
    if len(signal) == target_len:
        return signal
    if len(signal) > target_len:
        return signal[:target_len]
    return np.pad(signal, (0, target_len - len(signal)))


def process(signal: np.ndarray, sample_rate: int, args: argparse.Namespace) -> np.ndarray:
    mono = signal if signal.ndim == 1 else signal.mean(axis=1)
    insect = granular_stutter(
        mono,
        sample_rate,
        grain_ms=args.grain_ms,
        drop_prob=args.grain_drop,
        pitch_prob=args.grain_pitch_prob,
        pitch_step=args.grain_pitch_step,
        seed=args.seed,
    )
    insect = match_length(insect, len(mono))
    throat = ring_mod(insect, sample_rate, args.mod_freq)
    overload = hard_clip(throat, args.drive)
    filtered = apply_lowpass(overload, sample_rate, args.lowpass)
    dry = match_length(mono, len(filtered))
    mix = (filtered * args.wet) + (dry * (1.0 - args.wet))
    return mix


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Alien vocal transformer")
    parser.add_argument("input", type=Path, help="Input WAV/MP3 file")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output WAV path")
    parser.add_argument("--grain-ms", type=float, default=20.0, help="Grain size in milliseconds")
    parser.add_argument("--grain-drop", type=float, default=0.1, help="Probability of silencing a grain")
    parser.add_argument(
        "--grain-pitch-prob", type=float, default=0.7, help="Probability of pitching a grain"
    )
    parser.add_argument(
        "--grain-pitch-step", type=int, default=2, help="Sample skipping factor for pitch up"
    )
    parser.add_argument("--mod-freq", type=float, default=50.0, help="Ring modulator frequency in Hz")
    parser.add_argument("--drive", type=float, default=5.0, help="Hard clip drive amount")
    parser.add_argument("--lowpass", type=float, default=4000.0, help="Low-pass cutoff frequency")
    parser.add_argument("--wet", type=float, default=0.85, help="Wet mix ratio (0-1)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for repeatable glitches")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    input_path = args.input.expanduser().resolve()
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return 1
    try:
        sample_rate, audio = load_audio(input_path)
        processed = process(audio, sample_rate, args)
        output_path = (
            args.output.expanduser().resolve()
            if args.output
            else input_path.with_name(f"{input_path.stem}_alien.wav")
        )
        write_audio(output_path, sample_rate, processed)
        print(f"Alien render saved to {output_path}")
        return 0
    except Exception as exc:  # pragma: no cover - command line tool
        print(f"Processing failed: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
