#!/bin/bash
# Helper script to compile LaTeX report

echo "=== Lab 5 Report Compilation Script ==="
echo ""

# Check if pdflatex is installed
if ! command -v pdflatex &> /dev/null; then
    echo "Error: pdflatex not found. Installing texlive..."
    echo "This may take a few minutes..."
    sudo apt-get update
    sudo apt-get install -y texlive-latex-base texlive-latex-extra texlive-fonts-recommended
fi

echo "Compiling LaTeX report..."
echo ""

# Compile the report (run twice for references)
pdflatex -interaction=nonstopmode report.tex
pdflatex -interaction=nonstopmode report.tex

# Clean up auxiliary files
rm -f report.aux report.log report.out report.toc

if [ -f report.pdf ]; then
    echo ""
    echo "✓ Report compiled successfully: report.pdf"
    ls -lh report.pdf
else
    echo ""
    echo "✗ Report compilation failed"
    exit 1
fi