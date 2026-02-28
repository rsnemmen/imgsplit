# imgsplit

Split a tall JPEG or PNG image into page-sized slices ready for printing or embedding in A4 or Letter documents.

Scrolling screenshots and other vertically-stitched images are typically too tall to fit on a single page. `imgsplit` scales the image to fill the page width and cuts it into uniform slices, one per page.

## Requirements

- Python 3.10+
- [Pillow](https://python-pillow.org/) (`pip install Pillow`)

## Usage

```
python3 imgsplit.py [options] input
```

### Arguments

| Argument | Default | Description |
|---|---|---|
| `input` | — | Input JPEG or PNG file |
| `--format {A4,Letter}` | `A4` | Page format |
| `--dpi DPI` | `150` | Output resolution in DPI |
| `--margin MM` | `10` | Margin on each side in mm |
| `--output DIR` | input file's directory | Directory to write output files |
| `--prefix NAME` | input filename stem | Prefix for output filenames |

### Output

Pages are written as numbered PNG files:

```
{prefix}_001.png
{prefix}_002.png
...
```

The last page is padded with white if the image does not fill it completely.

## Examples

```bash
# Default: A4, 150 DPI, 10 mm margins
python3 imgsplit.py screenshot.png

# Letter format at 300 DPI
python3 imgsplit.py screenshot.png --format Letter --dpi 300

# No margins
python3 imgsplit.py screenshot.png --margin 0

# Write pages to a subdirectory with a custom prefix
python3 imgsplit.py screenshot.png --output ./pages --prefix slide
```

### Sample output

```
Input:          screenshot.png  (1560 × 19842 px)
Page format:    A4, 150 DPI, 10.0 mm margin
Printable area: 1122 × 1636 px
Output:         ./
  [1/9] screenshot_001.png
  ...
  [9/9] screenshot_009.png

Done — 9 page(s) written.
```

## How it works

1. The image is scaled so its width fills the printable area (page width minus margins).
2. The scaled image is sliced into vertical strips, each one page tall.
3. Transparent images (RGBA/PNG with alpha) are composited onto a white background before slicing.

## Page dimensions reference

| Format | Size | Printable area at 150 DPI, 10 mm margin |
|---|---|---|
| A4 | 210 × 297 mm | 1122 × 1636 px |
| Letter | 215.9 × 279.4 mm | 1146 × 1476 px |

At 300 DPI the pixel counts double in each dimension.
