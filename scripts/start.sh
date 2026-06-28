#!/bin/bash
set -e

MODE="local"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --docker|-d) MODE="docker"; shift ;;
        --help|-h) echo "Uso: ./start.sh [--docker | -d]"; exit 0 ;;
        *) echo "Opción desconocida: $1"; exit 1 ;;
    esac
done

if [ "$MODE" == "docker" ]; then
    echo "🐳 Levantando stack con Docker..."
    docker-compose up --build
    exit 0
fi

echo "🧹 Limpiando procesos anteriores en puertos 8000 y 5173..."
lsof -t -i:8000 2>/dev/null | xargs -r kill -9 2>/dev/null || true
lsof -t -i:5173 2>/dev/null | xargs -r kill -9 2>/dev/null || true
sleep 1

echo "🚀 Levantando backend y frontend en modo desarrollo local..."
echo ""

# Backend
cd backend
if [ ! -d ".venv" ]; then
    echo "❌ Entorno virtual no encontrado. Ejecuta primero:"
    echo "   cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo "🟢 Iniciando backend (FastAPI) en http://localhost:8000 ..."
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/rosa-backend.log 2>&1 &
BACKEND_PID=$!

# Esperar a que FastAPI esté listo (max 15s)
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend listo!"
        break
    fi
    sleep 0.5
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo ""
        echo "❌ Backend falló al arrancar. Logs:"
        tail -30 /tmp/rosa-backend.log
        echo ""
        echo "Si el error es 'Please enter the code', ejecuta primero:"
        echo "   cd backend && .venv/bin/python scripts/auth_telegram.py"
        echo ""
        # Matar frontend si se inicia luego
        break
    fi
done
cd ..

echo ""

# Frontend
cd frontend
if [ ! -d "node_modules" ]; then
    echo "❌ node_modules no encontrado. Ejecuta primero:"
    echo "   cd frontend && npm install"
    exit 1
fi

echo "🟡 Iniciando frontend (React + Vite + Tailwind) en http://localhost:5173 ..."
npm run dev > /tmp/rosa-frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo ""
echo "=========================================="
echo "✅ Rosa Flow Messages corriendo!"
echo "=========================================="
echo "  📡 Backend:  http://localhost:8000"
echo "  🎨 Frontend: http://localhost:5173"
echo "  📖 API Docs: http://localhost:8000/docs"
echo "  📝 Backend logs: tail -f /tmp/rosa-backend.log"
echo "  📝 Frontend logs: tail -f /tmp/rosa-frontend.log"
echo "=========================================="
echo ""
echo "Presiona Ctrl+C para detener ambos servicios."

# Al hacer Ctrl+C matar ambos procesos
trap "echo ''; echo '🛑 Deteniendo servicios...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit 0" INT TERM

wait
