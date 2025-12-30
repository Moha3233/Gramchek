#!/bin/bash

# Streamlit Cloud setup script
# This runs before your app starts

echo "🚀 Starting installation process..."

# Upgrade pip first (without any errors)
python -m pip install --upgrade pip

# Install required packages
pip install streamlit==1.28.0
pip install pdfplumber==0.10.3
pip install python-docx==1.1.0
pip install nltk==3.8.1
pip install pandas==2.1.4
pip install matplotlib==3.8.2
pip install pillow==10.1.0

# Download NLTK data (important!)
python -m nltk.downloader punkt
python -m nltk.downloader stopwords

echo "✅ Installation complete!"
