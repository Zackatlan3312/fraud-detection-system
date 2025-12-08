"""
Configuración del Sistema de Detección de Fraude
"""

# =====================================================
# CONFIGURACIÓN DE LA API
# =====================================================
API_HOST = "0.0.0.0"  # Escuchar en todas las interfaces
API_PORT = 8000

# =====================================================
# CONFIGURACIÓN DE CASSANDRA
# =====================================================
CASSANDRA_HOST = ['127.0.0.1']
CASSANDRA_PORT = 9042
CASSANDRA_KEYSPACE = 'finanzas'

# =====================================================
# PARÁMETROS DEL DETECTOR DE FRAUDE
# =====================================================

# Número de transacciones históricas a consultar para análisis
HISTORIAL_LIMITE = 50

# Umbral de Z-Score para detectar montos anómalos
# Un Z-Score > 3.0 significa que el monto está más de 3 desviaciones estándar
# por encima del promedio (muy inusual)
Z_SCORE_UMBRAL = 3.0

# Tiempo mínimo razonable para viajar entre ciudades (en minutos)
# Si hay transacciones en diferentes ciudades en menos de este tiempo,
# se considera sospechoso
TIEMPO_MINIMO_VIAJE = 30  # 30 minutos

# =====================================================
# UMBRALES DE DECISIÓN
# =====================================================

# Score de riesgo para rechazar automáticamente
UMBRAL_RECHAZO = 50.0

# Score de riesgo para marcar como revisión manual
UMBRAL_REVISION = 30.0

# =====================================================
# PESOS DE BANDERAS ROJAS
# =====================================================

PESO_ANOMALIA_GEOGRAFICA = 30.0
PESO_ANOMALIA_MONTO = 40.0
PESO_ANOMALIA_FRECUENCIA = 20.0
PESO_ANOMALIA_CATEGORIA = 10.0

# =====================================================
# CATEGORÍAS MCC DE ALTO RIESGO
# =====================================================

MCC_ALTO_RIESGO = [
    7995,  # Apuestas online / Casinos
    5993,  # Tiendas de cigarros
    7273,  # Servicios de citas
    5122,  # Drogas y medicamentos sin receta
    5933,  # Casas de empeño
]

# =====================================================
# CONFIGURACIÓN DE LOGGING
# =====================================================

LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = "fraud_detection.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# =====================================================
# CORS (Para desarrollo con React)
# =====================================================

CORS_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://localhost:8000",  # FastAPI
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]
