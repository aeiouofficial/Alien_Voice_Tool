# Alien Voice Tool

Python command line utility that morphs any vocal WAV or MP3 into an "alien creature" take while keeping the lyrics intelligible. The effect chain stacks granular stutter glitches, a 50 Hz ring modulator, diode-style distortion, and a smoothing low-pass filter.

## Prerequisites

1. **Python**: 3.10 or newer on PATH.
2. **Virtual environment (recommended)**:
   ```pwsh
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. **Dependencies**: install once per environment.
   ```pwsh
   pip install -r requirements.txt
   ```
4. **ffmpeg (only for MP3/flac/etc.)**: install from [ffmpeg.org](https://ffmpeg.org/) and ensure `ffmpeg.exe` is on PATH so `pydub` can decode compressed sources.
5. **Audio prep**: best results come from a mostly isolated vocal stem. Bounce to WAV to avoid extra decode steps when possible.

## Quick Start

1. Drop your vocal file into this folder.
2. Activate the virtual environment (if using one).
3. Run the tool:
   ```pwsh
   python alien_voice_tool.py "Sector 7 Protocol (Alien Mix).wav"
   ```
4. Find the rendered file next to the input as `<name>_alien.wav`.

## Detailed Usage

```
python alien_voice_tool.py input_audio.wav [options]
```

| Flag | Description | Default |
| --- | --- | --- |
| `-o`, `--output` | Destination WAV path | `<input>_alien.wav` |
| `--grain-ms` | Grain length in milliseconds | `20.0` |
| `--grain-drop` | Probability of muting a grain | `0.10` |
| `--grain-pitch-prob` | Chance a grain is pitched up | `0.70` |
| `--grain-pitch-step` | Sample skip factor when pitching up | `2` |
| `--mod-freq` | Ring modulator frequency (Hz) | `50.0` |
| `--drive` | Pre-clipping gain | `5.0` |
| `--lowpass` | Low-pass cutoff (Hz) | `4000.0` |
| `--wet` | Wet mix ratio (0 = dry, 1 = fully alien) | `0.85` |
| `--seed` | RNG seed for repeatable glitches | `None` |

Example keeping more dry vocal, lowering rumble, and forcing deterministic grains:

```pwsh
python alien_voice_tool.py input.mp3 -o output.wav --wet 0.6 --mod-freq 35 --seed 1337
```

## Recommended Workflow

- Convert MP3s to WAV first to avoid decode surprises (or install ffmpeg so the tool can do it).
- Use `--seed` while auditioning settings to make A/B comparisons easier.
- Lower `--drive` or raise `--lowpass` if you hear digital harshness; raise `--drive` for gnarlier insect tones.
- Blend the exported alien pass with your original vocal in a DAW to keep consonants crisp while adding texture.
- Batch process multiple takes via PowerShell: `Get-ChildItem *.wav | ForEach-Object { python alien_voice_tool.py $_.FullName }`.

## Troubleshooting

- **"Non-WAV input detected"**: install `pydub` and ffmpeg (or convert to WAV manually).
- **Clipping/distortion too heavy**: drop `--drive` below 3 or reduce `--wet`.
- **Effect sounds too random**: supply `--seed 42` or any integer to lock the granular pattern.
- **Result shorter/longer than source**: the tool trims/pads automatically, but ensure the source sample rate matches the expected vocal stem to avoid drift.
