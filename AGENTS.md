# Repository Guidelines

## Project Structure & Module Organization

This repository contains a small Python CLI for splitting tall images or PDFs into printable page slices.

- `imgsplit.py` is the main application and contains argument parsing, image/PDF loading, page splitting, OCR PDF generation, and CLI orchestration.
- `install.sh` installs the script into a user-local virtual environment and creates the `imgsplit` wrapper.
- `README.md` is the user-facing usage guide.
- `CLAUDE.md` contains agent-oriented implementation notes.
- `imgs/` stores README/demo assets and generated sample page images.

There is currently no dedicated `tests/` directory.

## Build, Test, and Development Commands

Run the CLI locally:

```bash
python3 imgsplit.py imgs/SCR-20260409-jrpo.png --output /tmp --prefix demo
```

Check command-line options:

```bash
python3 imgsplit.py --help
```

Run a syntax check:

```bash
python3 -m py_compile imgsplit.py
```

Verify OCR output manually by generating a PDF and extracting text with PyMuPDF. Use `/tmp` or another scratch directory for generated files.

## Coding Style & Naming Conventions

Use Python 3.10+ syntax and standard 4-space indentation. Keep the single-file structure unless a feature clearly justifies splitting modules. Prefer small functions with descriptive snake_case names, following existing patterns such as `load_pdf`, `split_image`, and `save_ocr_pdf`.

Use `Path` for filesystem paths. Keep CLI flags lowercase and hyphenated, for example `--images-only` and `--ocr-lang`.

No formatter or linter is configured; preserve the current style and avoid broad reformatting.

## Testing Guidelines

There is no formal test framework yet. For changes, run `python3 -m py_compile imgsplit.py` and at least one representative CLI command. For OCR-related work, verify that default PDF output has extractable text and that `--no-ocr` still produces an image-only PDF.

Do not overwrite tracked demo assets during testing. Write generated PDFs/PNGs to `/tmp` or `/private/tmp`.

## Commit & Pull Request Guidelines

Recent history uses concise imperative subjects, sometimes with a scope prefix, for example `Add searchable OCR PDF output` or `docs: add before/after images to README`.

Commits should include a short subject and, for behavioral changes, a body explaining user-visible behavior, dependency changes, and fallback/error handling. Keep unrelated generated images out of commits unless they intentionally update docs.

Pull requests should describe the change, list verification commands, note dependency changes such as Tesseract or PyMuPDF requirements, and include before/after screenshots only when README/demo visuals change.
