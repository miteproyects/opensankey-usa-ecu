#!/bin/bash
# SankeyViz — Lanzador Mac
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "Instalando dependencias (solo la primera vez)..."
python3 -m pip install streamlit plotly pandas yfinance kaleido --quiet

echo "Iniciando SankeyViz en tu navegador..."
python3 -m streamlit run "$DIR/sankey_app.py"
