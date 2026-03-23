#!/usr/bin/env python
"""imgsplit.py — Split a tall image into page-sized slices for A4 or Letter printing."""

import argparse
import math
import os
import sys
from pathlib import Path

from PIL import Image

PAGE_SIZES_MM = {
    "A4":     (210.0, 297.0),
    "Letter": (215.9, 279.4),
}


def mm_to_px(mm: float, dpi: int) -> int:
    return round(mm / 25.4 * dpi)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Split a tall JPEG/PNG image into page-sized slices.",
    )
    parser.add_argument("input", help="Input JPEG or PNG file")
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
        help="Output filename prefix (default: input filename stem)",
    )
    parser.add_argument(
        "--images-only", action="store_true",
        help="Save individual page PNGs instead of a combined PDF (PNGs are deleted by default)",
    )
    return parser.parse_args()


def load_image(path: str) -> Image.Image:
    suffix = Path(path).suffix.lower()
    if suffix not in (".jpg", ".jpeg", ".png"):
        sys.exit(f"Error: unsupported file type '{suffix}'. Only JPEG and PNG are accepted.")
    try:
        img = Image.open(path)
    except FileNotFoundError:
        sys.exit(f"Error: file not found: {path}")
    except Exception as e:
        sys.exit(f"Error opening image: {e}")

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


def main():
    args = parse_args()

    img = load_image(args.input)
    src_w, src_h = img.size

    page_w_mm, page_h_mm = PAGE_SIZES_MM[args.page_format]
    pw = mm_to_px(page_w_mm - 2 * args.margin, args.dpi)
    ph = mm_to_px(page_h_mm - 2 * args.margin, args.dpi)

    if pw <= 0 or ph <= 0:
        sys.exit("Error: margin is too large — printable area is zero or negative.")

    print(f"Input:          {args.input}  ({src_w} × {src_h} px)")
    print(f"Page format:    {args.page_format}, {args.dpi} DPI, {args.margin} mm margin")
    print(f"Printable area: {pw} × {ph} px")

    pages = split_image(img, pw, ph)

    input_path = Path(args.input)
    out_dir = Path(args.output) if args.output else input_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix if args.prefix else input_path.stem

    print(f"Output:         {out_dir}/")
    n = len(pages)
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


if __name__ == "__main__":
    main()
