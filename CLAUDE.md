# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`imgsplit.py` — a single-file Python CLI that splits a tall JPEG/PNG/PDF into page-sized slices for A4 or Letter printing, outputting a searchable multi-page PDF by default.

**Dependencies:** Pillow (`pip install Pillow`), PyMuPDF (`pip install PyMuPDF`), and Tesseract OCR. PyMuPDF is required for PDF input and for the default OCR-backed PDF output.

## Running

```bash
# Default: produces searchable {stem}.pdf, intermediate PNGs are deleted
python3 imgsplit.py image.png

# Produce the previous image-only PDF behavior
python3 imgsplit.py image.png --no-ocr

# Keep numbered PNGs instead of producing a PDF
python3 imgsplit.py image.png --images-only

# Common options
python3 imgsplit.py image.png --format Letter --dpi 300 --margin 5 --output ./out --prefix myname --ocr-lang eng
```

## Architecture

Everything lives in `imgsplit.py`:

- `parse_args()` — argparse setup; key args: `page_format`, `dpi`, `margin`, `output`, `prefix`, `images_only`, `no_ocr`, `ocr_lang`, `ocr_tessdata`
- `load_pdf(path, dpi)` — renders each PDF page at `dpi` via PyMuPDF, stacks pages vertically into one tall RGB image
- `load_image(path, dpi)` — routes `.pdf` to `load_pdf()`; for JPEG/PNG, opens and flattens any non-RGB mode (RGBA, P, L) onto a white background
- `split_image(img, pw, ph)` — scales image to printable width `pw`, slices into strips of height `ph`, pads the last strip with white; returns a list of in-memory `Image` objects
- `save_ocr_pdf(page_paths, pdf_path, dpi, language, tessdata)` — OCRs each intermediate PNG page with PyMuPDF/Tesseract, preserves PDF sizing via `Pixmap.set_dpi()`, and merges pages into the final searchable PDF
- `save_image_only_pdf(pages, pdf_path, dpi)` — preserves the old Pillow PDF writer used by `--no-ocr`
- `main()` — orchestrates: load → compute printable dimensions → split → write PNGs → (default) build OCR PDF then delete PNGs / (`--no-ocr`) build image-only PDF then delete PNGs / (`--images-only`) keep PNGs

Page dimensions are derived from `PAGE_SIZES_MM` dict (`A4`/`Letter`) minus `2 × margin`, converted via `mm_to_px(mm, dpi)`.

The default PDF is built from intermediate PNG page files using PyMuPDF's `Pixmap.pdfocr_tobytes()` Tesseract integration. OCR failures are reported and intermediate PNGs are kept for inspection. The Pillow-only PDF writer is still available with `--no-ocr`.
