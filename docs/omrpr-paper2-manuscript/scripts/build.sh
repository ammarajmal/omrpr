#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../manuscript"

pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

mkdir -p ../outputs
cp main.pdf ../outputs/main.pdf

echo "Built outputs/main.pdf"