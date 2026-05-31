#!/usr/bin/env bash
set -e

# Define paths for our self-bootstrapping runtime environment
EASEBUZZ_DIR="$HOME/.easebuzz"
RUNTIME_DIR="$EASEBUZZ_DIR/runtime"
BIN_LINK="/usr/local/bin/easebuzz"

echo "=========================================================="
echo "🚀 Installing Easebuzz Language-Independent Diagnostic CLI"
echo "=========================================================="

# 1. Ensure Python 3 is installed on the host system
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required to bootstrap this CLI utility."
    echo "Please install python3 using your system package manager (apt/brew) and try again."
    exit 1
fi

# 2. Create runtime sandbox directories
echo "📁 Setting up hidden runtime environments in $EASEBUZZ_DIR..."
mkdir -p "$EASEBUZZ_DIR/src"

# 3. Create an isolated Python Virtual Environment (Venv)
if [ ! -d "$RUNTIME_DIR" ]; then
    echo "📦 Provisioning isolated sandbox Python virtual environment..."
    python3 -m venv "$RUNTIME_DIR"
fi

# 4. Activate runtime context and install necessary standard UI packages
echo "⚙️ Installing runtime framework dependencies (typer, rich, requests, dynaconf)..."
"$RUNTIME_DIR/bin/pip" install --upgrade pip --quiet
"$RUNTIME_DIR/bin/pip" install requests typer rich dynaconf --quiet

# 5. Download / Deploy your core application logic scripts
# Note: Swap out this echo block with a real curl/git clone command from your repository when deploying!
echo "📥 Syncing core execution engine code components..."
cat << 'EOF' > "$EASEBUZZ_DIR/src/main.py"
import sys
import typer
# Simple routing wrapper script linking up your layout
try:
    from cmd.payments.make_payment import payments_app
    from config.config import config_app
except ImportError:
    # Fallback to structural setup directly if working out of a flat main file
    from payments import payments_app

app = typer.Typer(help="Easebuzz Merchant Diagnostic CLI Suite.")
app.add_typer(payments_app, name="payments")

if __name__ == "__main__":
    app()
EOF

# [CRITICAL STEP] Create the wrapper execution shell template
echo "executable stub generation..."
cat << EOF > "$EASEBUZZ_DIR/easebuzz-runner"
#!/usr/bin/env bash
# This wrapper executes using our dedicated isolated python runtime environment variables
export PYTHONPATH="$EASEBUZZ_DIR/src:\$PYTHONPATH"
exec "$RUNTIME_DIR/bin/python3" "$EASEBUZZ_DIR/src/main.py" "\$@"
EOF

chmod +x "$EASEBUZZ_DIR/easebuzz-runner"

# 6. Global Symlink Registration
echo "🔗 Creating a global execution symlink in system path..."
if [ -w "/usr/local/bin" ]; then
    ln -sf "$EASEBUZZ_DIR/easebuzz-runner" "$BIN_LINK"
else
    echo "🔑 Sudo privileges needed to create symlink at $BIN_LINK"
    sudo ln -sf "$EASEBUZZ_DIR/easebuzz-runner" "$BIN_LINK"
fi

echo "=========================================================="
echo "✨ Easebuzz Diagnostic Engine Installation Complete!"
echo "Type 'easebuzz --help' from any terminal directory to begin."
echo "=========================================================="