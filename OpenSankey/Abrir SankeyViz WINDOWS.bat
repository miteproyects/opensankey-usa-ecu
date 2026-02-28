@echo off
REM SankeyViz — Lanzador Windows
cd /d "%~dp0"

echo Instalando dependencias (solo la primera vez)...
python -m pip install streamlit plotly pandas yfinance kaleido --quiet

echo Iniciando SankeyViz...
python -m streamlit run "%~dp0sankey_app.py"
pause
