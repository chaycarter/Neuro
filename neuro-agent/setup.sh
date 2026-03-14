#!/bin/bash
# Neuro Agent - Setup Script
# Carter Sciences / neuro.reccy.dev

echo "Setting up Neuro Agent..."

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser binaries
playwright install chromium

# Copy env file if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "Created .env — add your ANTHROPIC_API_KEY to it before running."
fi

echo ""
echo "Setup complete."
echo ""
echo "To run Neuro Agent:"
echo "  1. Start Chrome with debugging:"
echo "     google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/neuro-chrome"
echo ""
echo "  2. Log into LinkedIn in that Chrome window."
echo ""
echo "  3. In this terminal:"
echo "     source .venv/bin/activate"
echo "     python main.py"
