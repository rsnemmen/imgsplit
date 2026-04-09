# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`imgsplit.py` — a single-file Python CLI that splits a tall JPEG/PNG/PDF into page-sized slices for A4 or Letter printing, outputting a multi-page PDF by default.

**Dependencies:** Pillow (`pip install Pillow`). PyMuPDF (`pip install PyMuPDF`) is required only for PDF input.

## Running

```bash
# Default: produces {stem}.pdf, intermediate PNGs are deleted
python3 imgsplit.py image.png

# Keep numbered PNGs instead of producing a PDF
python3 imgsplit.py image.png --images-only

# Common options
python3 imgsplit.py image.png --format Letter --dpi 300 --margin 5 --output ./out --prefix myname
```

## Architecture

Everything lives in `imgsplit.py`:

- `parse_args()` — argparse setup; key args: `page_format`, `dpi`, `margin`, `output`, `prefix`, `images_only`
- `load_pdf(path, dpi)` — renders each PDF page at `dpi` via PyMuPDF, stacks pages vertically into one tall RGB image
- `load_image(path, dpi)` — routes `.pdf` to `load_pdf()`; for JPEG/PNG, opens and flattens any non-RGB mode (RGBA, P, L) onto a white background
- `split_image(img, pw, ph)` — scales image to printable width `pw`, slices into strips of height `ph`, pads the last strip with white; returns a list of in-memory `Image` objects
- `main()` — orchestrates: load → compute printable dimensions → split → write PNGs → (default) build PDF from in-memory pages list then delete PNGs / (--images-only) keep PNGs

Page dimensions are derived from `PAGE_SIZES_MM` dict (`A4`/`Letter`) minus `2 × margin`, converted via `mm_to_px(mm, dpi)`.

The PDF is built entirely from the in-memory `pages` list using Pillow's `save_all=True` + `append_images` — no external PDF library needed.
