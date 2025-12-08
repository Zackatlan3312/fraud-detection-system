"""
Motor de detección de fraude basado en análisis de patrones
"""

import numpy as np
from datetime import datetime, timedelta
import sys
import os
import logging

# Agregar el directorio padre al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import (
    HISTORIAL_LIMITE,
    Z_SCORE_UMBRAL,
    TIEMPO_MINIMO_VIAJE,
    UMBRAL_RECHAZO,
    UMBRAL_REVISION,
    PESO_ANOMALIA_GEOGRAFICA,
    PESO_ANOMALIA_MONTO,
    PESO_ANOMALIA_FRECUENCIA,
    PESO_ANOMALIA_CATEGORIA,
    MCC_ALTO_RIESGO
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FraudDetector:
    """
    Motor de detección de fraude que analiza transacciones
    contra el historial del usuario usando 4 reglas principales
    """
    
    def __init__(self, db):
        """
        Inicializa el detector de fraude
        
        Args:
            db: Instancia de CassandraDB para consultar el historial
        """
        self.db = db
        logger.info("FraudDetector inicializado")
    
    def analizar_transaccion(self, transaccion):
        """
        Analiza una transacción y determina si es fraudulenta
        
        Args:
            transaccion (dict): Datos de la nueva transacción
            
        Returns:
            dict: Resultado del análisis con status, score y banderas
        """
        id_usuario = transaccion['id_usuario']
        
        # Obtener historial del usuario
        historial = self.db.obtener_historial_usuario(id_usuario, HISTORIAL_LIMITE)
        
        # Usuario nuevo - sin historial
        if len(historial) == 0:
            logger.info(f"Usuario nuevo: {id_usuario[:8]}... - Aprobado sin análisis")
            return {
                'status': 'APROBADO',
                'motivo': 'Usuario nuevo - sin historial para comparar',
                'score_riesgo': 0.0,
                'banderas_rojas': []
            }
        
        # Aplicar las 4 reglas de detección
        banderas_rojas = []
        score_riesgo = 0.0
        
        # Regla 1: Anomalía Geográfica
        if self._detectar_anomalia_geografica(transaccion, historial):
            banderas_rojas.append('ANOMALIA_GEOGRAFICA')
            score_riesgo += PESO_ANOMALIA_GEOGRAFICA
            logger.warning(f"Anomalía geográfica detectada: {transaccion['ciudad']}")
        
        # Regla 2: Anomalía de Monto (Z-Score)
        anomalia_monto, z_score = self._detectar_anomalia_monto(transaccion, historial)
        if anomalia_monto:
            banderas_rojas.append(f'ANOMALIA_MONTO (Z-Score: {z_score:.2f})')
            score_riesgo += PESO_ANOMALIA_MONTO
            logger.warning(f"Anomalía de monto detectada: ${transaccion['monto']} (Z-Score: {z_score:.2f})")
        
        # Regla 3: Anomalía de Frecuencia
        if self._detectar_anomalia_frecuencia(transaccion, historial):
            banderas_rojas.append('ANOMALIA_FRECUENCIA')
            score_riesgo += PESO_ANOMALIA_FRECUENCIA
            logger.warning("Anomalía de frecuencia detectada")
        
        # Regla 4: Anomalía de Categoría (MCC)
        if self._detectar_anomalia_categoria(transaccion, historial):
            banderas_rojas.append(f'ANOMALIA_CATEGORIA (MCC: {transaccion["mcc"]})')
            score_riesgo += PESO_ANOMALIA_CATEGORIA
            logger.warning(f"Anomalía de categoría detectada: MCC {transaccion['mcc']}")
        
        # Decidir el status final
        if score_riesgo >= UMBRAL_RECHAZO:
            status = 'RECHAZADO'
        elif score_riesgo >= UMBRAL_REVISION:
            status = 'REVISION_MANUAL'
        else:
            status = 'APROBADO'
        
        resultado = {
            'status': status,
            'score_riesgo': round(score_riesgo, 2),
            'banderas_rojas': banderas_rojas,
            'motivo': self._generar_motivo(status, banderas_rojas, score_riesgo)
        }
        
        logger.info(f"Análisis completado: {status} (Score: {score_riesgo}%)")
        return resultado
    
    def _detectar_anomalia_geografica(self, transaccion, historial):
        """
        Detecta si la ubicación es sospechosa comparada con la última transacción
        
        Considera sospechoso si:
        - La ciudad es diferente a la última transacción
        - Y el tiempo transcurrido es menor al mínimo para viajar
        
        Args:
            transaccion (dict): Nueva transacción
            historial (list): Historial del usuario
            
        Returns:
            bool: True si se detecta anomalía geográfica
        """
        if len(historial) == 0:
            return False
        
        # Obtener la última transacción
        ultima = historial[0]
        
        try:
            # Convertir timestamp string a datetime
            ultima_timestamp = datetime.fromisoformat(ultima['timestamp'])
            tiempo_transcurrido = datetime.now() - ultima_timestamp
            
            # Verificar viaje imposible
            if (transaccion['ciudad'] != ultima['ciudad'] and 
                tiempo_transcurrido < timedelta(minutes=TIEMPO_MINIMO_VIAJE)):
                
                logger.debug(f"Viaje imposible: {ultima['ciudad']} → {transaccion['ciudad']} en {tiempo_transcurrido}")
                return True
                
        except Exception as e:
            logger.error(f"Error en detección geográfica: {e}")
        
        return False
    
    def _detectar_anomalia_monto(self, transaccion, historial):
        """
        Detecta si el monto es anormalmente alto usando Z-Score
        
        Z-Score mide cuántas desviaciones estándar está un valor del promedio:
        - Z-Score < 2: Normal
        - Z-Score 2-3: Inusual
        - Z-Score > 3: Muy inusual (posible fraude)
        
        Args:
            transaccion (dict): Nueva transacción
            historial (list): Historial del usuario
            
        Returns:
            tuple: (bool, float) - (¿Es anómalo?, Z-Score)
        """
        if len(historial) < 3:
            return False, 0.0
        
        try:
            # Calcular estadísticas del historial
            montos = [float(t['monto']) for t in historial]
            promedio = np.mean(montos)
            desviacion = np.std(montos)
            
            # Evitar división por cero
            if desviacion == 0:
                desviacion = 1.0
            
            # Calcular Z-Score del nuevo monto
            nuevo_monto = float(transaccion['monto'])
            z_score = (nuevo_monto - promedio) / desviacion
            
            logger.debug(f"Estadísticas: Promedio=${promedio:.2f}, Desv=${desviacion:.2f}, Nuevo=${nuevo_monto}, Z={z_score:.2f}")
            
            # Detectar si está por encima del umbral
            if z_score > Z_SCORE_UMBRAL:
                return True, z_score
                
        except Exception as e:
            logger.error(f"Error en detección de monto: {e}")
        
        return False, 0.0
    
    def _detectar_anomalia_frecuencia(self, transaccion, historial):
        """
        Detecta si hay demasiadas transacciones en poco tiempo
        
        Considera sospechoso si:
        - La frecuencia actual es 5x mayor que el promedio histórico
        
        Args:
            transaccion (dict): Nueva transacción
            historial (list): Historial del usuario
            
        Returns:
            bool: True si se detecta anomalía de frecuencia
        """
        if len(historial) < 10:
            return False
        
        try:
            # Contar transacciones en la última hora
            ahora = datetime.now()
            transacciones_ultima_hora = 0
            
            for t in historial:
                timestamp = datetime.fromisoformat(t['timestamp'])
                if ahora - timestamp < timedelta(hours=1):
                    transacciones_ultima_hora += 1
            
            # Calcular promedio histórico de transacciones por hora
            # Asumimos que el historial cubre aproximadamente 24 horas
            promedio_por_hora = len(historial) / 24.0
            
            logger.debug(f"Frecuencia: {transacciones_ultima_hora} en última hora vs {promedio_por_hora:.2f} promedio")
            
            # Detectar ráfaga de transacciones (5x el promedio)
            if transacciones_ultima_hora > promedio_por_hora * 5:
                return True
                
        except Exception as e:
            logger.error(f"Error en detección de frecuencia: {e}")
        
        return False
    
    def _detectar_anomalia_categoria(self, transaccion, historial):
        """
        Detecta si la categoría MCC es inusual para este usuario
        
        Considera sospechoso si:
        - Es un MCC de alto riesgo (apuestas, etc.)
        - Y nunca se ha usado antes por este usuario
        
        Args:
            transaccion (dict): Nueva transacción
            historial (list): Historial del usuario
            
        Returns:
            bool: True si se detecta anomalía de categoría
        """
        if len(historial) < 5:
            return False
        
        try:
            # Obtener MCCs históricos
            mccs_historial = [t['mcc'] for t in historial]
            mccs_unicos = set(mccs_historial)
            
            nuevo_mcc = transaccion['mcc']
            
            # Si el MCC nunca se ha usado Y es de alto riesgo
            if nuevo_mcc not in mccs_unicos and nuevo_mcc in MCC_ALTO_RIESGO:
                logger.debug(f"MCC de alto riesgo no usado antes: {nuevo_mcc}")
                return True
                
        except Exception as e:
            logger.error(f"Error en detección de categoría: {e}")
        
        return False
    
    def _generar_motivo(self, status, banderas_rojas, score):
        """
        Genera un mensaje explicativo basado en el análisis
        
        Args:
            status (str): Estado de la transacción
            banderas_rojas (list): Lista de anomalías detectadas
            score (float): Score de riesgo
            
        Returns:
            str: Mensaje explicativo
        """
        if len(banderas_rojas) == 0:
            return "Transacción normal según el historial del usuario"
        
        if status == 'RECHAZADO':
            return f"RECHAZADO - Score de riesgo: {score}% - Anomalías: {', '.join(banderas_rojas)}"
        elif status == 'REVISION_MANUAL':
            return f"Requiere revisión manual - Score: {score}% - Anomalías: {', '.join(banderas_rojas)}"
        else:
            return f"Aprobado con {len(banderas_rojas)} banderas menores - Score: {score}%"
