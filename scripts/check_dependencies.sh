#!/bin/bash

# Dependency checker and auto-installer for clustering pipeline

echo "========================================"
echo "📦 Checking Python Dependencies"
echo "========================================"
echo ""

# Required packages
REQUIRED_PACKAGES="pandas numpy sklearn openpyxl openai tqdm dotenv"

# Check if packages are installed
echo "Checking: $REQUIRED_PACKAGES"
echo ""

python3 << 'EOF'
import sys

packages = {
    'pandas': 'pandas',
    'numpy': 'numpy',
    'sklearn': 'scikit-learn',
    'openpyxl': 'openpyxl',
    'openai': 'openai',
    'tqdm': 'tqdm',
    'dotenv': 'python-dotenv'
}

missing = []
installed = []

for import_name, pip_name in packages.items():
    try:
        __import__(import_name)
        installed.append(pip_name)
    except ImportError:
        missing.append(pip_name)

if installed:
    print("✅ Installed packages:")
    for pkg in installed:
        print(f"   - {pkg}")

if missing:
    print("")
    print("❌ Missing packages:")
    for pkg in missing:
        print(f"   - {pkg}")
    sys.exit(1)
else:
    print("")
    print("✅ All dependencies installed!")
    sys.exit(0)

EOF

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "========================================"
    echo "📥 Installing Missing Dependencies"
    echo "========================================"
    echo ""
    echo "This will install the following packages:"
    echo "  - From: requirements.txt"
    echo "  - Method: pip3 install --user"
    echo "  - Time: ~2-5 minutes (first time)"
    echo ""

    # Ask for confirmation (skip in non-interactive mode)
    if [ -t 0 ]; then
        read -p "Install now? (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Installation cancelled."
            echo ""
            echo "To install manually:"
            echo "  pip3 install -r requirements.txt --user"
            exit 1
        fi
    fi

    # Install
    echo ""
    echo "Installing..."
    pip3 install -r requirements.txt --user

    # Verify
    echo ""
    echo "Verifying installation..."
    python3 -c "import pandas, numpy, sklearn, openpyxl, openai, tqdm"

    if [ $? -eq 0 ]; then
        echo ""
        echo "========================================"
        echo "✅ Installation Complete!"
        echo "========================================"
        echo ""
        echo "You can now run:"
        echo "  python3 scripts/pipeline.py --input data/file.xlsx"
    else
        echo ""
        echo "========================================"
        echo "❌ Installation Failed"
        echo "========================================"
        echo ""
        echo "Please install manually:"
        echo "  pip3 install -r requirements.txt --user"
        echo ""
        echo "Or contact support for assistance."
        exit 1
    fi
else
    echo ""
    echo "Ready to run clustering pipeline!"
fi
