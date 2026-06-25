# Listening examples: Neural Refinement of Time-Frequency Representations for Audio Time-Stretching

Supplementary audio for the master thesis (TMA4900, NTNU, Department of Mathematical Sciences).
Author: Håvard Fossdal. June 2026.

**Browse the clips here:** https://hfossdal.github.io/time-stretch-listening/

The page lets you play the same held-out clip through every compared method and filter by domain
(speech or music) and by case (controlled 1×, stretch 0.75×, stretch 0.50×). Only one clip plays at
a time, so A/B comparison stays clean.

## What you are listening for

These are diagnostic listening examples, not a formal listener study. The main cue is sharp
upper-band roughness on speech consonants (sibilants and stop releases) under stretch, and how far
the residual-mined adapter reduces it as the correction gain α rises.

## Methods in each example

| File | Method |
| --- | --- |
| `00_original_clip.wav` | Original / reference |
| `01_interpolation_baseline_bigvgan.wav` | Linear interpolation + BigVGAN |
| `Full-skip_2D_U-Net.wav` | Full-skip 2D U-Net + BigVGAN |
| `Complex-STFT_CRN.wav` | Complex-STFT CRN + inverse STFT |
| `Residual-mined_adapter_alpha_1.00.wav` | Residual-mined adapter, α = 1.0 |
| `Residual-mined_adapter_alpha_1.50.wav` | Residual-mined adapter, α = 1.5 |
| `Residual-mined_adapter_alpha_2.00.wav` | Residual-mined adapter, α = 2.0 |

## Folder layout

```
audio/
  SPEECH_idx0_1.00x_controlled_inpainting/
  SPEECH_idx0_stretch_0.75x/
  SPEECH_idx0_stretch_0.50x/
  ...
  MUSIC_idx0_1.00x_controlled_inpainting/
  ...
index.html          generated comparison page
generate_site.py    rebuilds index.html from the audio/ tree
```

## Rebuilding the page

If you add, rename, or remove clips, regenerate the page:

```
python generate_site.py audio
```

The script reads every subfolder of `audio/`, maps filenames to method labels, and writes a fresh
`index.html`. Paths stay relative, so it works the same locally and on GitHub Pages.

## Source data

Speech clips come from EARS, LibriTTS, and VCTK. Music clips come from MUSDB18-HQ mixtures. Where a
dataset license does not allow redistributing the original audio, the source identifiers and the
generation commands are recorded instead of the raw files.

## Music attribution

Music examples are modified excerpts from MUSDB18-HQ tracks whose licences permit non-commercial
redistribution with attribution and share-alike terms:

- The Easton Ellises (Baumi) — SDRNR, CC BY-NC-SA 3.0
- The Easton Ellises — Falcon 69, CC BY-NC-SA 3.0
- A Classic Education — NightOwl, CC BY-NC-SA

The excerpts were processed by the time-stretching and neural-refinement methods described in the
thesis. The original artists do not endorse these processed versions.

Sources: [SigSep MUSDB track list](https://raw.githubusercontent.com/sigsep/website/master/content/datasets/assets/tracklist.csv)
and [Creative Commons BY-NC-SA 3.0](https://creativecommons.org/licenses/by-nc-sa/3.0/).
