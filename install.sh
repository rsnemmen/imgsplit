#!/usr/bin/env bash
# install.sh — imgsplit installer
#
# Installs imgsplit into a self-contained venv under ~/.local/share/imgsplit
# and a thin wrapper at ~/.local/bin/imgsplit.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/rsnemmen/imgsplit/main/install.sh | bash
#
# Re-run the same command to upgrade.
# Uninstall: rm -rf ~/.local/share/imgsplit ~/.local/bin/imgsplit
#
# Dependencies (Pillow, PyMuPDF) are intentionally left unpinned;
# upgrade-on-reinstall is a feature.
#
set -euo pipefail

main() {
  REPO_RAW="${REPO_RAW:-https://raw.githubusercontent.com/rsnemmen/imgsplit/main}"
  APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/imgsplit"
  BIN_DIR="$HOME/.local/bin"
  VENV="$APP_DIR/venv"
  SCRIPT="$APP_DIR/imgsplit.py"
  WRAPPER="$BIN_DIR/imgsplit"

  require_cmd
  require_python_version
  warn_if_existing_imgsplit
  make_dirs
  ensure_venv
  download_script
  write_wrapper
  path_hint
  success_banner
}

require_cmd() {
  local missing=0
  for cmd in python3 curl; do
    if ! command -v "$cmd" > /dev/null 2>&1; then
      printf 'Error: %s not found. Please install it and re-run.\n' "$cmd" >&2
      missing=1
    fi
  done
  [ "$missing" -eq 0 ] || exit 1
}

require_python_version() {
  if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    local ver
    ver="$(python3 -c 'import sys; print(".".join(str(x) for x in sys.version_info[:3]))' 2>/dev/null || printf 'unknown')"
    printf 'Error: Python 3.10+ is required (found %s).\n' "$ver" >&2
    exit 1
  fi
}

warn_if_existing_imgsplit() {
  local existing
  existing="$(command -v imgsplit 2>/dev/null || true)"
  if [ -n "$existing" ] && [ "$existing" != "$WRAPPER" ]; then
    printf 'Warning: an existing "imgsplit" was found at %s.\n' "$existing"
    printf '  It will be shadowed by (or shadow) the newly installed wrapper at %s.\n' "$WRAPPER"
  fi
}

make_dirs() {
  mkdir -p "$APP_DIR" "$BIN_DIR"
}

ensure_venv() {
  if [ ! -x "$VENV/bin/python" ]; then
    printf '  Creating virtual environment...\n'
    python3 -m venv "$VENV"
  else
    printf '  Reusing existing virtual environment.\n'
  fi
  printf '  Installing/upgrading Python dependencies...\n'
  "$VENV/bin/python" -m pip install --quiet --upgrade pip
  "$VENV/bin/python" -m pip install --quiet --upgrade Pillow PyMuPDF
}

download_script() {
  printf '  Downloading imgsplit.py...\n'
  curl -fsSL --proto '=https' --tlsv1.2 --retry 3 -o "${SCRIPT}.tmp" "$REPO_RAW/imgsplit.py"
  if [ ! -s "${SCRIPT}.tmp" ] || [ "$(wc -c < "${SCRIPT}.tmp")" -le 1000 ]; then
    printf 'Error: downloaded file appears truncated or empty.\n' >&2
    rm -f "${SCRIPT}.tmp"
    exit 1
  fi
  mv "${SCRIPT}.tmp" "$SCRIPT"
  chmod +x "$SCRIPT"
}

write_wrapper() {
  # Use an unquoted heredoc delimiter so $VENV and $SCRIPT expand NOW (install
  # time) to absolute paths. The wrapper has no runtime dependency on env vars.
  # "$@" is escaped so it lands verbatim in the wrapper, not expanded here.
  cat > "${WRAPPER}.tmp" <<EOF
#!/usr/bin/env bash
exec "$VENV/bin/python" "$SCRIPT" "\$@"
EOF
  mv "${WRAPPER}.tmp" "$WRAPPER"
  chmod +x "$WRAPPER"
}

path_hint() {
  case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *)
      printf '\n'
      printf '  NOTE: %s is not on your PATH.\n' "$BIN_DIR"
      printf '  Add the following line to your shell configuration file:\n\n'
      printf '    export PATH="$HOME/.local/bin:$PATH"\n\n'
      local shell_name
      shell_name="${SHELL##*/}"
      case "$shell_name" in
        zsh)
          printf '  Then run:  source ~/.zshrc\n'
          ;;
        bash)
          printf '  Suggested files: ~/.bashrc  (interactive shells)\n'
          printf '                   ~/.bash_profile  (macOS login shells)\n'
          printf '  Then run:  source ~/.bashrc  (or ~/.bash_profile)\n'
          ;;
        *)
          printf '  (Check your shell'"'"'s documentation for the right config file.)\n'
          ;;
      esac
      ;;
  esac
}

success_banner() {
  printf '\n'
  printf 'imgsplit installed successfully.\n'
  printf '  Script:  %s\n' "$SCRIPT"
  printf '  Wrapper: %s\n' "$WRAPPER"
  printf '\n'
  printf 'Try it:\n'
  printf '  imgsplit --help\n'
}

main "$@"
