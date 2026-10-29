"""
API REST para el sistema de detección de fraude
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import uvicorn
import sys
import os
import logging

# Agregar el directorio padre al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import CassandraDB
from src.fraud_detector import FraudDetector
from config.config import API_HOST, API_PORT, CORS_ORIGINS

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==========================================
# MODELOS DE DATOS PARA LA API
# ==========================================

class Transaccion(BaseModel):
    """Modelo de datos para una transacción"""
    id_usuario: str = Field(..., description="UUID del usuario")
    monto: float = Field(..., gt=0, description="Monto de la transacción")
    moneda: str = Field(..., description="Código de moneda (MXN, USD, EUR)")
    comercio: str = Field(..., description="Nombre del comercio")
    ciudad: str = Field(..., description="Ciudad de la transacción")
    pais: str = Field(..., description="País de la transacción")
    mcc: int = Field(..., description="Merchant Category Code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id_usuario": "550e8400-e29b-41d4-a716-446655440000",
                "monto": 150.50,
                "moneda": "MXN",
                "comercio": "Walmart",
                "ciudad": "CDMX",
                "pais": "Mexico",
                "mcc": 5411
            }
        }


class RespuestaAnalisis(BaseModel):
    """Modelo de respuesta del análisis de fraude"""
    status: str
    score_riesgo: float
    banderas_rojas: List[str]
    motivo: str
    transaccion_guardada: bool


class EstadisticasUsuario(BaseModel):
    """Modelo para estadísticas de un usuario"""
    id_usuario: str
    total_transacciones: int
    monto_total: float
    monto_promedio: float
    ciudades_frecuentes: List[str]
    comercios_frecuentes: List[str]


# ==========================================
# INICIALIZAR FASTAPI
# ==========================================

app = FastAPI(
    title="Sistema de Detección de Fraude",
    description="API REST para detectar fraudes en transacciones bancarias en tiempo real",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para desarrollo con React
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancias globales
db = CassandraDB()
detector = FraudDetector(db)

# Decisiones tomadas desde que arrancó la API. Las rechazadas no se guardan
# en Cassandra, así que este es el único lugar donde se cuentan.
conteo_decisiones = {"APROBADO": 0, "REVISION_MANUAL": 0, "RECHAZADO": 0}


# ==========================================
# EVENTOS DE CICLO DE VIDA
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Se ejecuta al iniciar la API"""
    logger.info("=" * 60)
    logger.info("Iniciando API de Detección de Fraude...")
    logger.info("=" * 60)
    
    if db.connect():
        logger.info("✓ Conexión a Cassandra establecida")
    else:
        logger.error("✗ Error conectando a Cassandra")
        logger.error("Asegúrate de que Cassandra esté corriendo y las tablas creadas")


@app.on_event("shutdown")
async def shutdown_event():
    """Se ejecuta al cerrar la API"""
    logger.info("Cerrando API...")
    db.disconnect()
    logger.info("Servidor cerrado correctamente")


# ==========================================
# ENDPOINTS
# ==========================================

@app.get("/", tags=["General"])
async def root():
    """Endpoint de bienvenida con información del sistema"""
    return {
        "servicio": "API de Detección de Fraude en Tiempo Real",
        "version": "2.0.0",
        "estado": "activo",
        "endpoints": {
            "documentacion": "/docs",
            "analisis": "/analizar-transaccion",
            "historial": "/historial/{id_usuario}",
            "transaccion": "/transaccion/{id_transaccion}",
            "usuarios": "/usuarios",
            "estadisticas": "/estadisticas/{id_usuario}",
            "resumen": "/resumen",
            "salud": "/health"
        }
    }


@app.get("/health", tags=["General"])
async def health_check():
    """Endpoint para verificar el estado del servicio"""
    # Se hace una consulta real: que exista la sesión no garantiza que
    # Cassandra siga arriba
    if not db.esta_disponible():
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected"}
        )

    return {
        "status": "healthy",
        "database": "connected",
        "keyspace": db.session.keyspace
    }


@app.post("/analizar-transaccion", response_model=RespuestaAnalisis, tags=["Análisis"])
async def analizar_transaccion(transaccion: Transaccion):
    """
    Analiza una transacción y determina si es fraudulenta
    
    Retorna:
    - APROBADO: Transacción normal
    - REVISION_MANUAL: Requiere revisión humana
    - RECHAZADO: Probable fraude
    """
    try:
        # Convertir a diccionario
        transaccion_dict = transaccion.model_dump()
        
        logger.info(f"Analizando transacción: ${transaccion.monto} {transaccion.moneda} - {transaccion.comercio}")
        
        # Analizar con el detector de fraude
        resultado = detector.analizar_transaccion(transaccion_dict)
        conteo_decisiones[resultado['status']] += 1

        # Guardar la transacción si es aprobada o requiere revisión
        transaccion_guardada = False
        if resultado['status'] in ['APROBADO', 'REVISION_MANUAL']:
            guardado = db.insertar_transaccion(transaccion_dict)
            transaccion_guardada = guardado['success']
            
            if transaccion_guardada:
                logger.info(f"Transacción guardada: {guardado['id_transaccion']}")
        
        return {
            **resultado,
            "transaccion_guardada": transaccion_guardada
        }
        
    except Exception as e:
        logger.error(f"Error analizando transacción: {e}")
        raise HTTPException(status_code=500, detail=f"Error analizando transacción: {str(e)}")


@app.get("/historial/{id_usuario}", tags=["Consultas"])
async def obtener_historial(id_usuario: str, limite: Optional[int] = 50):
    """
    Obtiene el historial de transacciones de un usuario
    
    Args:
        id_usuario: UUID del usuario
        limite: Número máximo de transacciones a retornar (default: 50)
    """
    try:
        if limite < 1 or limite > 1000:
            raise HTTPException(status_code=400, detail="Límite debe estar entre 1 y 1000")
        
        historial = db.obtener_historial_usuario(id_usuario, limite)
        
        return {
            "id_usuario": id_usuario,
            "total_transacciones": len(historial),
            "transacciones": historial
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {str(e)}")


@app.get("/transaccion/{id_transaccion}", tags=["Consultas"])
async def obtener_transaccion(id_transaccion: str):
    """
    Obtiene los detalles de una transacción específica
    
    Args:
        id_transaccion: UUID de la transacción
    """
    try:
        transaccion = db.obtener_transaccion_por_id(id_transaccion)
        
        if transaccion is None:
            raise HTTPException(status_code=404, detail="Transacción no encontrada")
        
        return transaccion
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo transacción: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo transacción: {str(e)}")


@app.get("/usuarios", tags=["Consultas"])
async def obtener_usuarios(limite: Optional[int] = 100):
    """
    Obtiene la lista de usuarios que tienen transacciones en el sistema
    
    Args:
        limite: Número máximo de usuarios a retornar
    """
    try:
        if limite < 1 or limite > 1000:
            raise HTTPException(status_code=400, detail="Límite debe estar entre 1 y 1000")
        
        usuarios = db.obtener_usuarios_con_transacciones(limite)
        
        return {
            "total_usuarios": len(usuarios),
            "usuarios": usuarios
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo usuarios: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo usuarios: {str(e)}")


@app.get("/estadisticas/{id_usuario}", response_model=EstadisticasUsuario, tags=["Análisis"])
async def obtener_estadisticas_usuario(id_usuario: str):
    """
    Obtiene estadísticas sobre las transacciones de un usuario
    """
    try:
        historial = db.obtener_historial_usuario(id_usuario, 1000)
        
        if len(historial) == 0:
            raise HTTPException(status_code=404, detail="Usuario sin transacciones")
        
        # Calcular estadísticas
        montos = [t['monto'] for t in historial]
        ciudades = [t['ciudad'] for t in historial]
        comercios = [t['comercio'] for t in historial]
        
        # Ciudades más frecuentes
        from collections import Counter
        ciudades_freq = Counter(ciudades).most_common(5)
        comercios_freq = Counter(comercios).most_common(5)
        
        return {
            "id_usuario": id_usuario,
            "total_transacciones": len(historial),
            "monto_total": round(sum(montos), 2),
            "monto_promedio": round(sum(montos) / len(montos), 2),
            "ciudades_frecuentes": [c[0] for c in ciudades_freq],
            "comercios_frecuentes": [c[0] for c in comercios_freq]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")


@app.get("/resumen", tags=["Consultas"])
async def obtener_resumen():
    """
    Resumen para el dashboard

    - transacciones_guardadas: lo que hay en Cassandra (null si no respondió)
    - aprobadas, en_revision, rechazadas: análisis hechos desde que arrancó la API
    """
    return {
        "transacciones_guardadas": db.contar_transacciones(),
        "aprobadas": conteo_decisiones["APROBADO"],
        "en_revision": conteo_decisiones["REVISION_MANUAL"],
        "rechazadas": conteo_decisiones["RECHAZADO"]
    }


# ==========================================
# FUNCIÓN PRINCIPAL
# ==========================================

def iniciar_servidor():
    """Inicia el servidor Uvicorn"""
    logger.info(f"Iniciando servidor en http://{API_HOST}:{API_PORT}")
    logger.info("Documentación disponible en http://{API_HOST}:{API_PORT}/docs")
    
    uvicorn.run(
        app, 
        host=API_HOST, 
        port=API_PORT,
        log_level="info"
    )


if __name__ == "__main__":
    iniciar_servidor()
