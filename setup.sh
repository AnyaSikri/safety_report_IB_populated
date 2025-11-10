#!/bin/bash

# Setup script for IB-to-DSR Automation System

echo "=================================="
echo "IB-to-DSR Setup Script"
echo "=================================="

# Create necessary directories
echo "Creating directory structure..."
mkdir -p data/input/{ib_pdf,dsr_template,mapping}
mkdir -p data/intermediate
mkdir -p data/output
mkdir -p tests

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    echo "OPENAI_API_KEY=your-api-key-here" > .env
    echo "⚠ WARNING: Please edit .env and add your OpenAI API key!"
fi

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OpenAI API key"
echo "2. Run the pipeline:"
echo "   python main.py \\"
echo "     --ib-pdf investigative_brochure.pdf \\"
echo "     --template Drug_Safety_Report_Template.docx \\"
echo "     --mapping IB_to_DSR_Manual_Mapping.md \\"
echo "     --output data/output/DSR_Populated.docx"
echo ""

