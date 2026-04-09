#!/usr/bin/env python
"""imgsplit.py — Split a tall image into page-sized slices for A4 or Letter printing."""

import argparse
import math
import os
import sys
from pathlib import Path

from PIL import Image

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

PAGE_SIZES_MM = {
    "A4":     (210.0, 297.0),
    "Letter": (215.9, 279.4),
}


def mm_to_px(mm: float, dpi: int) -> int:
    return round(mm / 25.4 * dpi)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Split a tall JPEG/PNG/PDF into page-sized slices.",
    )
    parser.add_argument("inputs", nargs="+", metavar="input",
                        help="Input JPEG, PNG, or PDF file(s)")
    parser.add_argument(
        "--format", dest="page_format", choices=["A4", "Letter"], default="Letter",
        help="Page format (default: Letter)",
    )
    parser.add_argument(
        "--dpi", type=int, default=150,
        help="Output resolution in DPI (default: 150)",
    )
    parser.add_argument(
        "--margin", type=float, default=10.0,
        help="Margin on each side in mm (default: 10)",
    )
    parser.add_argument(
        "--output", metavar="DIR", default=None,
        help="Output directory (default: same directory as input file)",
    )
    parser.add_argument(
        "--prefix", default=None,
        help="Output filename prefix (default: input filename stem; cannot be used with multiple inputs)",
    )
    parser.add_argument(
        "--images-only", action="store_true",
        help="Save individual page PNGs instead of a combined PDF (PNGs are deleted by default)",
    )
    return parser.parse_args()


def _detect_pdf_source_dpi(doc) -> float:
    """Probe embedded bitmap density on page 0 to estimate the PDF's native DPI."""
    try:
        page = doc[0]
        images = page.get_images(full=True)
    except Exception:
        return 0.0
    best = 0.0
    for img_info in images:
        try:
            bbox = page.get_image_bbox(img_info)
        except Exception:
            continue
        if bbox.width <= 0 or bbox.height <= 0:
            continue
        img_w_px, img_h_px = img_info[2], img_info[3]
        if img_w_px <= 0 or img_h_px <= 0:
            continue
        best = max(best, img_w_px * 72.0 / bbox.width, img_h_px * 72.0 / bbox.height)
    return best


def load_pdf(path: str, dpi: int) -> Image.Image:
    """Render a PDF (single or multi-page) to a single tall RGB PIL image."""
    if fitz is None:
        raise ValueError(
            "PDF input requires PyMuPDF. Install it with: pip install PyMuPDF"
        )
    try:
        doc = fitz.open(path)
    except FileNotFoundError:
        raise ValueError(f"file not found: {path}")
    except Exception as e:
        raise ValueError(f"error opening PDF: {e}")

    if doc.page_count == 0:
        doc.close()
        raise ValueError(f"PDF has no pages: {path}")

    # Render at the output DPI, or the PDF's native bitmap DPI if higher (so
    # embedded high-res bitmaps aren't thrown away before split_image sees them).
    # Capped at 600 DPI to keep memory bounded on pathological inputs.
    source_dpi = _detect_pdf_source_dpi(doc)
    render_dpi = min(max(dpi, round(source_dpi)), 600)

    zoom = render_dpi / 72.0  # PDF user-space unit is 1/72 inch
    matrix = fitz.Matrix(zoom, zoom)
    rendered = []
    for page in doc:
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        rendered.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    doc.close()

    if len(rendered) == 1:
        return rendered[0]

    # Stack pages vertically, centering narrower pages on a white background
    max_w = max(p.width for p in rendered)
    total_h = sum(p.height for p in rendered)
    combined = Image.new("RGB", (max_w, total_h), (255, 255, 255))
    y = 0
    for p in rendered:
        combined.paste(p, ((max_w - p.width) // 2, y))
        y += p.height
    return combined


def load_image(path: str, dpi: int) -> Image.Image:
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        return load_pdf(path, dpi)
    if suffix not in (".jpg", ".jpeg", ".png"):
        raise ValueError(
            f"unsupported file type '{suffix}'. Only JPEG, PNG, and PDF are accepted."
        )
    try:
        img = Image.open(path)
    except FileNotFoundError:
        raise ValueError(f"file not found: {path}")
    except Exception as e:
        raise ValueError(f"error opening image: {e}")

    # Flatten to RGB (handles RGBA, P, L, etc.) with a white background
    if img.mode != "RGB":
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode in ("RGBA", "LA"):
            background.paste(img, mask=img.split()[-1])
        else:
            background.paste(img.convert("RGB"))
        img = background

    return img


def split_image(img: Image.Image, pw: int, ph: int) -> list[Image.Image]:
    """Scale img to width pw and split into vertical strips of height ph."""
    src_w, src_h = img.size
    scaled_h = round(src_h * pw / src_w)
    scaled = img.resize((pw, scaled_h), Image.LANCZOS)

    n_pages = math.ceil(scaled_h / ph)
    pages = []
    for i in range(n_pages):
        top = i * ph
        bottom = min(top + ph, scaled_h)
        strip = scaled.crop((0, top, pw, bottom))

        # Pad the last (possibly short) strip with white
        if strip.height < ph:
            page = Image.new("RGB", (pw, ph), (255, 255, 255))
            page.paste(strip, (0, 0))
            strip = page

        pages.append(strip)

    return pages


def process_file(input_path: str, args, pw: int, ph: int, prefix: str) -> bool:
    """Process a single input file. Returns True on success, False on handled failure."""
    try:
        img = load_image(input_path, args.dpi)
    except ValueError as e:
        print(f"Error: {e}")
        return False

    src_w, src_h = img.size
    print(f"Input:          {input_path}  ({src_w} × {src_h} px)")
    print(f"Page format:    {args.page_format}, {args.dpi} DPI, {args.margin} mm margin")
    print(f"Printable area: {pw} × {ph} px")

    pages = split_image(img, pw, ph)

    in_path = Path(input_path)
    out_dir = Path(args.output) if args.output else in_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output:         {out_dir}/")
    n = len(pages)
    try:
        for i, page in enumerate(pages, start=1):
            out_path = out_dir / f"{prefix}_{i:03d}.png"
            page.save(out_path, format="PNG")
            filled = round(30 * i / n)
            bar = "█" * filled + "░" * (30 - filled)
            print(f"\r  [{bar}] {i}/{n}", end="", flush=True)
        print()

        if args.images_only:
            print(f"\nDone — {len(pages)} PNG(s) written.")
        else:
            pdf_path = out_dir / f"{prefix}.pdf"
            pages[0].save(
                pdf_path,
                format="PDF",
                save_all=True,
                append_images=pages[1:],
                resolution=args.dpi,
            )
            print(f"PDF:            {pdf_path.name}")
            for i in range(1, len(pages) + 1):
                (out_dir / f"{prefix}_{i:03d}.png").unlink()
            print(f"\nDone — {len(pages)}-page PDF written.")
    except OSError as e:
        print(f"\nError writing output: {e}")
        return False

    return True


def main():
    args = parse_args()

    if len(args.inputs) > 1 and args.prefix is not None:
        sys.exit("Error: --prefix cannot be used with multiple input files.")

    page_w_mm, page_h_mm = PAGE_SIZES_MM[args.page_format]
    pw = mm_to_px(page_w_mm - 2 * args.margin, args.dpi)
    ph = mm_to_px(page_h_mm - 2 * args.margin, args.dpi)

    if pw <= 0 or ph <= 0:
        sys.exit("Error: margin is too large — printable area is zero or negative.")

    batch = len(args.inputs) > 1
    n_total = len(args.inputs)
    failures = 0

    for idx, input_path in enumerate(args.inputs, start=1):
        if batch:
            print(f"=== [{idx}/{n_total}] {input_path} ===")

        prefix = args.prefix if args.prefix else Path(input_path).stem
        ok = process_file(input_path, args, pw, ph, prefix)
        if not ok:
            failures += 1

        if batch and idx < n_total:
            print()

    if batch:
        succeeded = n_total - failures
        print(f"\nBatch complete — {succeeded}/{n_total} succeeded.")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
