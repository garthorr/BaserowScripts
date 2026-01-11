#!/bin/bash
# Setup script for BaserowScripts
# This creates a virtual environment and installs all dependencies

set -e

echo "=================================================="
echo "BaserowScripts Setup"
echo "=================================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo ""
echo "Installing dependencies..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel -q

# Install required packages
pip install -r requirements.txt

echo ""
echo "✓ All dependencies installed"
echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Copy and configure your environment file:"
echo "   cp .env.example .env"
echo "   # Edit .env with your Baserow credentials"
echo ""
echo "3. Run the scripts:"
echo "   python update_contacts.py --excel-file your_file.xlsx --dry-run"
echo "   python deduplicate_table.py --identifying-field Email --dry-run"
echo ""
