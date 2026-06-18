#!/usr/bin/env bash
# Install addchin. Run directly:
#   curl -fsSL https://raw.githubusercontent.com/bartaat/addchin/main/install.sh | bash
set -euo pipefail

REPO="https://github.com/bartaat/addchin"

have() { command -v "$1" >/dev/null 2>&1; }

if ! have uv; then
  echo "Installing uv (https://docs.astral.sh/uv/)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # uv installs to ~/.local/bin or ~/.cargo/bin; make it visible for this run
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if have uv; then
  echo "Installing addchin with uv..."
  uv tool install --from "git+$REPO" addchin
  echo
  echo "Installed. Ensure your uv tools dir is on PATH (uv tool update-shell), then run:"
  echo "    addchin --check"
  exit 0
fi

echo "uv unavailable; falling back to a pip virtual environment."
BIN_DIR="$HOME/.local/bin"
VENV_DIR="$HOME/.local/share/addchin-venv"
mkdir -p "$BIN_DIR"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
"$VENV_DIR/bin/pip" install "git+$REPO"
ln -sf "$VENV_DIR/bin/addchin" "$BIN_DIR/addchin"
echo
echo "Installed: $BIN_DIR/addchin"
case ":$PATH:" in
  *":$BIN_DIR:"*) echo "Run: addchin --check" ;;
  *) echo "Add ~/.local/bin to your PATH, then run: addchin --check" ;;
esac
