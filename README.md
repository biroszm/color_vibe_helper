# Bloomette — Colour Mood Finder

A small toolkit for exploring the colour mood of images. It pairs a Python
indexer that extracts Lab-colour features from a folder of images with a
browser-based canvas where you can sketch, pick colours, and match images by
their overall palette.

## What's in the repo

- **`pic_calculator.py`** — scans a folder of images and writes
  `image_index.csv` containing average Lab values, per-channel histograms,
  and the dominant quantized colours for each image.
- **`canvas.html`** — the Bloomette web UI: a single-file canvas with a
  custom colour picker, palette legend, and onboarding flow built in the
  Bloomette editorial style.
- **`logo.svg`** — the Bloomette wordmark/logo used in the UI.

## Using the image indexer

Requires Python 3 and [Pillow](https://pillow.readthedocs.io/):

```bash
pip install pillow
python pic_calculator.py [input_folder] [output_csv]
```

Both arguments are optional. By default it scans the folder the script lives
in and writes `image_index.csv` next to it.

Useful flags:

- `--bins` — histogram bins per Lab channel (default `8`)
- `--resize-max` — resize the longest image side before analysis (default `300`)
- `--top-colors` — number of dominant colours to keep (default `6`)
- `--white-threshold` — RGB threshold above which pixels are treated as
  white background and ignored (default `245`)

Supported formats: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`, `.gif`, `.tiff`.

## Using the canvas

Open `canvas.html` in any modern browser — no build step required.

## Authors

A side project brainstormed together by:

- **Marton** ([@biroszm](https://github.com/biroszm)) — core architecture and engineering
- **Aco Hsu** ([@aco-h](https://github.com/aco-h)) — UI/UX and visual design

