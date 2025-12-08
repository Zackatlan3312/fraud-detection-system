"""
Módulo de conexión y operaciones con Apache Cassandra
"""

import os
import sys

# Variables de entorno para deshabilitar extensiones C de Cassandra
# (necesario en algunos entornos)
os.environ['CASS_DRIVER_NO_CYTHON'] = '1'
os.environ['CASS_DRIVER_NO_EXTENSIONS'] = '1'

# Agregar el directorio padre al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, ConsistencyLevel
import uuid
from datetime import datetime
import logging

from config.config import (
    CASSANDRA_HOST,
    CASSANDRA_PORT,
    CASSANDRA_KEYSPACE
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CassandraDB:
    """
    Clase para manejar la conexión y operaciones con Cassandra
    """
    
    def __init__(self):
        self.cluster = None
        self.session = None
        self._prepared_statements = {}
        
    def connect(self):
        """
        Conectar a Cassandra y preparar statements
        
        Returns:
            bool: True si la conexión fue exitosa, False en caso contrario
        """
        try:
            self.cluster = Cluster(
                CASSANDRA_HOST, 
                port=CASSANDRA_PORT,
                protocol_version=4,
                connect_timeout=10
            )
            self.session = self.cluster.connect()
            self.session.set_keyspace(CASSANDRA_KEYSPACE)
            
            # Preparar los statements para mejor performance
            self._preparar_statements()
            
            logger.info(f"Conectado a Cassandra - Keyspace: {CASSANDRA_KEYSPACE}")
            return True
            
        except Exception as e:
            logger.error(f"Error conectando a Cassandra: {e}")
            return False
    
    def _preparar_statements(self):
        """Prepara los prepared statements para mejor performance"""
        self._prepared_statements['insert_usuario'] = self.session.prepare("""
            INSERT INTO transacciones_por_usuario 
            (id_usuario, timestamp, id_transaccion, monto, moneda, comercio, ciudad, pais, mcc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        
        self._prepared_statements['insert_id'] = self.session.prepare("""
            INSERT INTO transacciones_por_id
            (id_transaccion, id_usuario, timestamp, monto, moneda, comercio, ciudad, pais, mcc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        
        self._prepared_statements['select_historial'] = self.session.prepare("""
            SELECT monto, ciudad, pais, timestamp, mcc, comercio, moneda, id_transaccion
            FROM transacciones_por_usuario
            WHERE id_usuario = ?
            LIMIT ?
        """)
        
        self._prepared_statements['select_por_id'] = self.session.prepare("""
            SELECT *
            FROM transacciones_por_id
            WHERE id_transaccion = ?
        """)
    
    def disconnect(self):
        """Desconectar de Cassandra"""
        if self.cluster:
            self.cluster.shutdown()
            logger.info("Desconectado de Cassandra")
    
    def insertar_transaccion(self, transaccion):
        """
        Inserta una transacción en ambas tablas (patrón de duplicación de Cassandra)
        
        Args:
            transaccion (dict): Diccionario con los datos de la transacción
        
        Returns:
            dict: Resultado de la operación con 'success' y 'id_transaccion' o 'error'
        """
        try:
            # Generar IDs y timestamp
            id_transaccion = uuid.uuid1()  # TimeUUID
            id_usuario = uuid.UUID(transaccion['id_usuario'])
            timestamp = datetime.now()
            monto = float(transaccion['monto'])
            
            # Ejecutar ambas inserciones
            self.session.execute(self._prepared_statements['insert_usuario'], (
                id_usuario, 
                timestamp, 
                id_transaccion,
                monto, 
                transaccion['moneda'], 
                transaccion['comercio'],
                transaccion['ciudad'], 
                transaccion['pais'], 
                transaccion['mcc']
            ))
            
            self.session.execute(self._prepared_statements['insert_id'], (
                id_transaccion, 
                id_usuario, 
                timestamp,
                monto, 
                transaccion['moneda'], 
                transaccion['comercio'],
                transaccion['ciudad'], 
                transaccion['pais'], 
                transaccion['mcc']
            ))
            
            logger.info(f"Transacción insertada: {id_transaccion}")
            return {
                'success': True, 
                'id_transaccion': str(id_transaccion),
                'timestamp': timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error insertando transacción: {e}")
            return {'success': False, 'error': str(e)}
    
    def obtener_historial_usuario(self, id_usuario, limite=50):
        """
        Obtiene el historial de transacciones de un usuario ordenado por fecha
        
        Args:
            id_usuario (str): UUID del usuario
            limite (int): Número máximo de transacciones a retornar
        
        Returns:
            list: Lista de diccionarios con las transacciones
        """
        try:
            id_usuario_uuid = uuid.UUID(id_usuario)
            rows = self.session.execute(
                self._prepared_statements['select_historial'], 
                (id_usuario_uuid, limite)
            )
            
            historial = []
            for row in rows:
                historial.append({
                    'id_transaccion': str(row.id_transaccion) if hasattr(row, 'id_transaccion') else None,
                    'monto': float(row.monto),
                    'moneda': row.moneda,
                    'ciudad': row.ciudad,
                    'pais': row.pais,
                    'timestamp': row.timestamp.isoformat(),
                    'mcc': row.mcc,
                    'comercio': row.comercio
                })
            
            logger.info(f"Historial obtenido: {len(historial)} transacciones para usuario {id_usuario[:8]}...")
            return historial
            
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return []
    
    def obtener_transaccion_por_id(self, id_transaccion):
        """
        Obtiene una transacción específica por su ID
        
        Args:
            id_transaccion (str): UUID de la transacción
        
        Returns:
            dict: Diccionario con los datos de la transacción o None si no existe
        """
        try:
            id_trans_uuid = uuid.UUID(id_transaccion)
            row = self.session.execute(
                self._prepared_statements['select_por_id'], 
                (id_trans_uuid,)
            ).one()
            
            if row:
                return {
                    'id_transaccion': str(row.id_transaccion),
                    'id_usuario': str(row.id_usuario),
                    'timestamp': row.timestamp.isoformat(),
                    'monto': float(row.monto),
                    'moneda': row.moneda,
                    'comercio': row.comercio,
                    'ciudad': row.ciudad,
                    'pais': row.pais,
                    'mcc': row.mcc
                }
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo transacción: {e}")
            return None
    
    def obtener_usuarios_con_transacciones(self, limite=100):
        """
        Obtiene una lista de usuarios que tienen transacciones
        
        Args:
            limite (int): Número máximo de usuarios a retornar
        
        Returns:
            list: Lista de UUIDs de usuarios
        """
        try:
            query = f"""
                SELECT DISTINCT id_usuario 
                FROM {CASSANDRA_KEYSPACE}.transacciones_por_usuario 
                LIMIT {limite}
            """
            
            rows = self.session.execute(query)
            usuarios = [str(row.id_usuario) for row in rows]
            
            logger.info(f"Usuarios encontrados: {len(usuarios)}")
            return usuarios
            
        except Exception as e:
            logger.error(f"Error obteniendo usuarios: {e}")
            return []
    
    def __enter__(self):
        """Context manager: entrada"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: salida"""
        self.disconnect()
