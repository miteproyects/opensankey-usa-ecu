#!/bin/bash
# SuperComp V4 Launcher
cd "$(dirname "$0")"

echo "🚀 SuperComp V4..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no instalado"
    read -p "Presiona Enter..."
    exit 1
fi

if ! python3 -c "import flask" 2>/dev/null; then
    pip3 install flask -q
fi

if ! python3 -c "import playwright" 2>/dev/null; then
    pip3 install playwright -q
    python3 -m playwright install chromium
fi

if ! python3 -c "import pytesseract" 2>/dev/null; then
    pip3 install pytesseract pillow -q
fi

PORT=8889

if curl -s http://localhost:$PORT > /dev/null 2>&1; then
    echo "⚠️  Servidor ya activo"
    open "http://localhost:$PORT"
    exit 0
fi

echo "⏳ Iniciando..."
python3 app.py &

for i in {1..30}; do
    if curl -s http://localhost:$PORT > /dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

echo "🌐 Abriendo navegador..."
open "http://localhost:$PORT"

echo ""
echo "✅ Listo!"
echo ""
echo "📋 El programa:"
echo "   • Guarda localmente"
echo "   • Abre Chrome y navega a Supercias"
echo "   • Captura el CAPTCHA para que lo escribas"
echo "   • Intenta clic en 'Información anual presentada'"
echo "   • Guarda screenshots BEFORE/AFTER para verificación"
echo "   • Mantiene Chrome ABIERTO"
echo ""
echo "📸 Verifica el clic comparando:"
echo "   BEFORE_CLICK_*.png vs AFTER_CLICK_*.png"
echo "   en la carpeta 'R.U.C. consultados/'"
echo ""
echo "📖 Lee COMO_USAR.txt para más detalles"
echo ""
echo "⚠️  Ctrl+C para detener el servidor"
echo ""

wait $!
