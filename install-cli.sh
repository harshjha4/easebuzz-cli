#!/bin/bash
set -e

GITHUB_USERNAME="harshjha4"
GITHUB_REPO="easebuzz-cli"

echo "Bootstrapping Easebuzz CLI (Standalone Binary)..."

# 1. Detect Operating System and Architecture
OS="$(uname -s)"
ARCH="$(uname -m)"

echo "Detected System: $OS on $ARCH"

if [ "$OS" = "Linux" ]; then
    BINARY_NAME="easebuzz-cli-linux"
elif [ "$OS" = "Darwin" ]; then
    if [ "$ARCH" = "arm64" ]; then
        BINARY_NAME="easebuzz-mac-arm" # For Apple Silicon (M1/M2/M3)
    else
        BINARY_NAME="easebuzz-mac-intel" # For older Intel Macs
    fi
else
    echo "Unsupported OS for this bash script. For Windows, please download the .exe directly."
    exit 1
fi

# 2. Construct the GitHub Releases Download URL
# This fetches the binary from the "Latest" release tag on your repo
DOWNLOAD_URL="https://github.com/${GITHUB_USERNAME}/${GITHUB_REPO}/releases/latest/download/${BINARY_NAME}"

# 3. Download the Binary
echo "⬇️ Downloading ${BINARY_NAME}..."
if ! curl -fsSL -o easebuzz "$DOWNLOAD_URL"; then
    echo "Download failed. Make sure you have uploaded '${BINARY_NAME}' to your GitHub Releases page."
    exit 1
fi

# 4. Make the file natively executable
chmod +x easebuzz

# 5. Move it directly into the system's global execution path
BIN_DIR="/usr/local/bin"
echo "🔐 Linking global executable footprint to ${BIN_DIR}/easebuzz (requires sudo permission)..."

if [ -w "$BIN_DIR" ]; then
    mv easebuzz "$BIN_DIR/easebuzz"
else
    sudo mv easebuzz "$BIN_DIR/easebuzz"
fi

echo ""
echo "🎉 Success! The Easebuzz CLI is installed."
echo "👉 Run 'easebuzz --help' from any terminal window to get started."