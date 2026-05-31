#!/bin/bash
set -e

# ==============================================================================
# Easebuzz CLI - Self-Bootstrapping Installer
# ==============================================================================

# ⚠️ UPDATE THESE VARIABLES TO MATCH YOUR ACTUAL GITHUB REPOSITORY ⚠️
GITHUB_USERNAME="harshjha4"
GITHUB_REPO="easebuzz-cli"
BRANCH="master"
TARBALL_URL="https://github.com/${GITHUB_USERNAME}/${GITHUB_REPO}/tarball/${BRANCH}"

# Local System Paths
EASEBUZZ_DIR="$HOME/.easebuzz"
RUNTIME_DIR="$EASEBUZZ_DIR/runtime"
SRC_DIR="$EASEBUZZ_DIR/src"
LAUNCHER_SCRIPT="$EASEBUZZ_DIR/easebuzz-launcher"
BIN_LINK="/usr/local/bin/easebuzz"

echo "⚡ Bootstrapping Easebuzz CLI Runtime Environment..."

# 1. System Dependency Checks
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required. Please install Python 3 and try again."
    exit 1
fi

if ! command -v curl &> /dev/null || ! command -v tar &> /dev/null; then
    echo "❌ Error: 'curl' and 'tar' are required to download and extract the CLI."
    exit 1
fi

# 2. Build the Directory Structure
echo "📁 Setting up local directories..."
mkdir -p "$EASEBUZZ_DIR"
mkdir -p "$SRC_DIR"

# 3. Download and Extract Source Code
echo "🚚 Fetching latest core source modules from GitHub..."
TMP_TAR="$EASEBUZZ_DIR/source.tar.gz"
curl -fsSL "$TARBALL_URL" -o "$TMP_TAR"

# GitHub tarballs wrap everything inside a root folder (e.g., username-repo-hash)
# --strip-components=1 removes that top folder so 'main.py' lands directly in SRC_DIR
tar -xzf "$TMP_TAR" --strip-components=1 -C "$SRC_DIR"
rm "$TMP_TAR"

# 4. Provision the Isolated Virtual Environment
if [ ! -d "$RUNTIME_DIR" ]; then
    echo "📦 Provisioning isolated Python runtime sandbox..."
    python3 -m venv "$RUNTIME_DIR"
fi

# 5. Install Dependencies from requirements.txt
echo "📥 Syncing locked third-party dependencies inside sandbox..."
"$RUNTIME_DIR/bin/pip" install --upgrade pip --quiet
if [ -f "$SRC_DIR/requirements.txt" ]; then
    "$RUNTIME_DIR/bin/pip" install -r "$SRC_DIR/requirements.txt" --quiet
else
    # Fallback if requirements.txt goes missing
    "$RUNTIME_DIR/bin/pip" install typer rich requests dynaconf --quiet
fi

# 6. Generate the Global Launcher Wrapper
echo "🔗 Registering easebuzz terminal launcher script..."
cat << EOF > "$LAUNCHER_SCRIPT"
#!/usr/bin/env bash
# This launcher forces the system to execute our raw source code using our sandboxed interpreter
export PYTHONPATH="$SRC_DIR"
exec "$RUNTIME_DIR/bin/python" "$SRC_DIR/main.py" "\$@"
EOF

# Make the launcher executable
chmod +x "$LAUNCHER_SCRIPT"

# 7. Expose Globally to System $PATH via Symlink
echo "🔐 Linking global executable (may require sudo password)..."
if [ -L "$BIN_LINK" ] || [ -f "$BIN_LINK" ]; then
    sudo rm -f "$BIN_LINK"
fi

sudo ln -s "$LAUNCHER_SCRIPT" "$BIN_LINK"

echo ""
echo "🎉 Success! The self-bootstrapping runtime environment is live."
echo "👉 Run 'easebuzz --help' from any terminal window to get started."