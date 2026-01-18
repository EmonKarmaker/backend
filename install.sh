#!/bin/bash
echo "Installing dependencies..."
pip install -r requirements.txt

# Install ffmpeg (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y ffmpeg

echo "Installation complete!"