#!/bin/bash

# Script de inicio rápido para Linux/Mac

echo "========================================"
echo "Sistema de Detección de Fraude"
echo "========================================"
echo ""

# Verificar si Cassandra está corriendo
echo "[1/4] Verificando Cassandra..."
if ! docker ps | grep -q cassandra-fraud; then
    echo "Cassandra no está corriendo. Iniciando..."
    docker start cassandra-fraud
    sleep 10
else
    echo "✓ Cassandra ya está corriendo"
fi

# Activar entorno virtual
echo ""
echo "[2/4] Activando entorno virtual..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "✗ ERROR: Entorno virtual no encontrado."
    echo "Ejecuta primero: python -m venv venv"
    exit 1
fi

# Iniciar backend en background
echo ""
echo "[3/4] Iniciando backend..."
cd "$(dirname "$0")"
python src/api.py &
BACKEND_PID=$!
echo "Backend iniciado (PID: $BACKEND_PID)"

# Esperar un poco
sleep 3

# Iniciar frontend
echo ""
echo "[4/4] Iniciando frontend..."
cd frontend
npm start &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "✓ Sistema iniciado correctamente!"
echo "========================================"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Documentación: http://localhost:8000/docs"
echo ""
echo "Para detener el sistema:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "O presiona Ctrl+C"

# Mantener el script vivo
wait
