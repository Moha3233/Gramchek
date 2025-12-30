#!/bin/bash

# Streamlit Cloud Setup Script
# This installs all dependencies for the ATS Resume Scanner

echo "🚀 Starting setup for ATS Resume Scanner..."

# Upgrade pip and setuptools
python -m pip install --upgrade pip setuptools wheel

# Install core dependencies (PyMuPDF instead of pdfplumber)
pip install streamlit==1.28.0
pip install PyMuPDF==1.23.8
pip install python-docx==1.1.0
pip install nltk==3.8.1
pip install pandas==2.1.4
pip install matplotlib==3.8.2
pip install pillow==10.1.0

# Download NLTK data
echo "📥 Downloading NLTK datasets..."
python -c "import nltk; nltk.download('punkt', quiet=True)"
python -c "import nltk; nltk.download('stopwords', quiet=True)"
python -c "import nltk; nltk.download('averaged_perceptron_tagger', quiet=True)"

echo "✅ Setup completed successfully!"
