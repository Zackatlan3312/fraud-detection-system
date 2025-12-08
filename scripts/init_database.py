"""
Script de inicialización de la base de datos Cassandra
Crea el keyspace y las tablas necesarias
"""

import os
import sys
import time

# Agregar el directorio padre al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from config.config import CASSANDRA_HOST, CASSANDRA_PORT, CASSANDRA_KEYSPACE


def esperar_cassandra(max_intentos=30):
    """Espera a que Cassandra esté disponible"""
    print("Esperando a que Cassandra esté disponible...")
    
    for intento in range(max_intentos):
        try:
            cluster = Cluster(CASSANDRA_HOST, port=CASSANDRA_PORT, protocol_version=4)
            session = cluster.connect()
            print(f"✓ Cassandra está disponible (intento {intento + 1})")
            cluster.shutdown()
            return True
        except Exception as e:
            if intento < max_intentos - 1:
                print(f"  Intento {intento + 1}/{max_intentos} - Esperando...")
                time.sleep(2)
            else:
                print(f"✗ Error: No se pudo conectar a Cassandra después de {max_intentos} intentos")
                print(f"  Detalle: {e}")
                return False
    
    return False


def crear_keyspace(session):
    """Crea el keyspace si no existe"""
    print(f"\nCreando keyspace '{CASSANDRA_KEYSPACE}'...")
    
    query = f"""
        CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE}
        WITH replication = {{
            'class': 'SimpleStrategy',
            'replication_factor': 1
        }}
    """
    
    try:
        session.execute(query)
        print(f"✓ Keyspace '{CASSANDRA_KEYSPACE}' creado exitosamente")
        return True
    except Exception as e:
        print(f"✗ Error creando keyspace: {e}")
        return False


def crear_tabla_transacciones_por_usuario(session):
    """Crea la tabla de transacciones indexadas por usuario"""
    print("\nCreando tabla 'transacciones_por_usuario'...")
    
    query = f"""
        CREATE TABLE IF NOT EXISTS {CASSANDRA_KEYSPACE}.transacciones_por_usuario (
            id_usuario uuid,
            timestamp timestamp,
            id_transaccion timeuuid,
            monto decimal,
            moneda text,
            comercio text,
            ciudad text,
            pais text,
            mcc int,
            PRIMARY KEY (id_usuario, timestamp, id_transaccion)
        ) WITH CLUSTERING ORDER BY (timestamp DESC)
        AND comment = 'Transacciones ordenadas por usuario y fecha (para historial)'
    """
    
    try:
        session.execute(query)
        print("✓ Tabla 'transacciones_por_usuario' creada exitosamente")
        return True
    except Exception as e:
        print(f"✗ Error creando tabla: {e}")
        return False


def crear_tabla_transacciones_por_id(session):
    """Crea la tabla de transacciones indexadas por ID"""
    print("\nCreando tabla 'transacciones_por_id'...")
    
    query = f"""
        CREATE TABLE IF NOT EXISTS {CASSANDRA_KEYSPACE}.transacciones_por_id (
            id_transaccion timeuuid PRIMARY KEY,
            id_usuario uuid,
            timestamp timestamp,
            monto decimal,
            moneda text,
            comercio text,
            ciudad text,
            pais text,
            mcc int
        ) WITH comment = 'Transacciones indexadas por ID (para búsqueda rápida)'
    """
    
    try:
        session.execute(query)
        print("✓ Tabla 'transacciones_por_id' creada exitosamente")
        return True
    except Exception as e:
        print(f"✗ Error creando tabla: {e}")
        return False


def verificar_tablas(session):
    """Verifica que las tablas se hayan creado correctamente"""
    print("\nVerificando tablas creadas...")
    
    query = f"""
        SELECT table_name 
        FROM system_schema.tables 
        WHERE keyspace_name = '{CASSANDRA_KEYSPACE}'
    """
    
    try:
        rows = session.execute(query)
        tablas = [row.table_name for row in rows]
        
        print(f"\nTablas encontradas en keyspace '{CASSANDRA_KEYSPACE}':")
        for tabla in tablas:
            print(f"  ✓ {tabla}")
        
        # Verificar que existan las tablas esperadas
        tablas_esperadas = ['transacciones_por_usuario', 'transacciones_por_id']
        todas_existen = all(tabla in tablas for tabla in tablas_esperadas)
        
        if todas_existen:
            print("\n✓ Todas las tablas necesarias están creadas")
            return True
        else:
            print("\n✗ Faltan algunas tablas")
            return False
            
    except Exception as e:
        print(f"✗ Error verificando tablas: {e}")
        return False


def main():
    """Función principal de inicialización"""
    print("=" * 60)
    print("INICIALIZACIÓN DE BASE DE DATOS - Sistema de Detección de Fraude")
    print("=" * 60)
    
    # Paso 1: Esperar a que Cassandra esté disponible
    if not esperar_cassandra():
        print("\n✗ FALLO: Cassandra no está disponible")
        print("\nAsegúrate de que Cassandra esté corriendo:")
        print("  docker run --name cassandra-fraud -p 9042:9042 -d cassandra:latest")
        sys.exit(1)
    
    # Paso 2: Conectar a Cassandra
    try:
        cluster = Cluster(CASSANDRA_HOST, port=CASSANDRA_PORT, protocol_version=4)
        session = cluster.connect()
        print(f"\n✓ Conectado a Cassandra en {CASSANDRA_HOST[0]}:{CASSANDRA_PORT}")
    except Exception as e:
        print(f"\n✗ Error conectando a Cassandra: {e}")
        sys.exit(1)
    
    # Paso 3: Crear keyspace
    if not crear_keyspace(session):
        cluster.shutdown()
        sys.exit(1)
    
    # Paso 4: Usar el keyspace
    session.set_keyspace(CASSANDRA_KEYSPACE)
    
    # Paso 5: Crear tablas
    if not crear_tabla_transacciones_por_usuario(session):
        cluster.shutdown()
        sys.exit(1)
    
    if not crear_tabla_transacciones_por_id(session):
        cluster.shutdown()
        sys.exit(1)
    
    # Paso 6: Verificar
    if not verificar_tablas(session):
        cluster.shutdown()
        sys.exit(1)
    
    # Cerrar conexión
    cluster.shutdown()
    
    print("\n" + "=" * 60)
    print("✓ INICIALIZACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 60)
    print("\nPuedes ahora:")
    print("  1. Generar datos de prueba: python src/data_generator.py")
    print("  2. Iniciar la API: python src/api.py")
    print("\n")


if __name__ == "__main__":
    main()
