#!/usr/bin/env bash

cd "$(dirname "$0")/../manuscript"

rm -f *.aux *.bbl *.blg *.log *.out *.toc *.lof *.lot *.fls *.fdb_latexmk *.synctex.gz

echo "Cleaned LaTeX auxiliary files"