"""
Generador de datos de prueba para el sistema de detección de fraude
"""

import random
import uuid
import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio padre al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import CassandraDB


class DataGenerator:
    """
    Generador de datos de prueba realistas para testing del sistema
    """
    
    def __init__(self):
        self.db = CassandraDB()
        
        # Catálogo de ciudades mexicanas
        self.ciudades_mexico = [
            {'ciudad': 'CDMX', 'pais': 'Mexico'},
            {'ciudad': 'Guadalajara', 'pais': 'Mexico'},
            {'ciudad': 'Monterrey', 'pais': 'Mexico'},
            {'ciudad': 'Veracruz', 'pais': 'Mexico'},
            {'ciudad': 'Puebla', 'pais': 'Mexico'},
            {'ciudad': 'Cancun', 'pais': 'Mexico'},
            {'ciudad': 'Tijuana', 'pais': 'Mexico'},
            {'ciudad': 'Merida', 'pais': 'Mexico'},
        ]
        
        # Catálogo de ciudades internacionales
        self.ciudades_internacionales = [
            {'ciudad': 'Paris', 'pais': 'Francia'},
            {'ciudad': 'Nueva York', 'pais': 'Estados Unidos'},
            {'ciudad': 'Londres', 'pais': 'Reino Unido'},
            {'ciudad': 'Tokio', 'pais': 'Japon'},
            {'ciudad': 'Madrid', 'pais': 'Espana'},
            {'ciudad': 'Buenos Aires', 'pais': 'Argentina'},
            {'ciudad': 'Sao Paulo', 'pais': 'Brasil'},
        ]
        
        # Tipos de comercios con sus MCC
        self.comercios_normales = [
            {'nombre': 'Oxxo', 'mcc': 5411},
            {'nombre': 'Walmart', 'mcc': 5411},
            {'nombre': 'Soriana', 'mcc': 5411},
            {'nombre': 'Restaurant Los Arcos', 'mcc': 5812},
            {'nombre': 'Tacos El Paisa', 'mcc': 5812},
            {'nombre': 'Starbucks', 'mcc': 5814},
            {'nombre': 'Gasolina Pemex', 'mcc': 5541},
            {'nombre': 'Amazon', 'mcc': 5999},
            {'nombre': 'Netflix', 'mcc': 4899},
            {'nombre': 'Uber', 'mcc': 4121},
            {'nombre': 'Farmacia Guadalajara', 'mcc': 5912},
        ]
        
        # Comercios de alto riesgo
        self.comercios_riesgo = [
            {'nombre': 'Casino Online', 'mcc': 7995},
            {'nombre': 'Apuestas Deportivas', 'mcc': 7995},
            {'nombre': 'Cigarreria Premium', 'mcc': 5993},
        ]
    
    def generar_transaccion_normal(self, id_usuario, ciudad_base=None):
        """
        Genera una transacción normal (comportamiento típico)
        
        Args:
            id_usuario (str): UUID del usuario
            ciudad_base (str, optional): Ciudad base del usuario
        
        Returns:
            dict: Transacción generada
        """
        if ciudad_base is None:
            ubicacion = random.choice(self.ciudades_mexico)
        else:
            # 80% en la ciudad base, 20% en otra ciudad mexicana
            if random.random() < 0.8:
                ubicacion = {'ciudad': ciudad_base, 'pais': 'Mexico'}
            else:
                ubicacion = random.choice(self.ciudades_mexico)
        
        comercio = random.choice(self.comercios_normales)
        
        transaccion = {
            'id_usuario': id_usuario,
            'monto': round(random.uniform(20, 500), 2),
            'moneda': 'MXN',
            'comercio': comercio['nombre'],
            'ciudad': ubicacion['ciudad'],
            'pais': ubicacion['pais'],
            'mcc': comercio['mcc']
        }
        
        return transaccion
    
    def generar_transaccion_fraudulenta(self, id_usuario, tipo_fraude=None):
        """
        Genera una transacción fraudulenta (comportamiento anómalo)
        
        Args:
            id_usuario (str): UUID del usuario
            tipo_fraude (str, optional): Tipo específico de fraude a simular
        
        Returns:
            dict: Transacción fraudulenta generada
        """
        if tipo_fraude is None:
            tipo_fraude = random.choice(['monto_alto', 'ubicacion_extrana', 'categoria_riesgo', 'combinado'])
        
        if tipo_fraude == 'monto_alto':
            # Monto anormalmente alto
            ubicacion = random.choice(self.ciudades_mexico)
            comercio = random.choice(self.comercios_normales)
            transaccion = {
                'id_usuario': id_usuario,
                'monto': round(random.uniform(5000, 15000), 2),
                'moneda': 'MXN',
                'comercio': comercio['nombre'],
                'ciudad': ubicacion['ciudad'],
                'pais': ubicacion['pais'],
                'mcc': comercio['mcc']
            }
        
        elif tipo_fraude == 'ubicacion_extrana':
            # Transacción en el extranjero
            ubicacion = random.choice(self.ciudades_internacionales)
            comercio = random.choice(self.comercios_normales)
            transaccion = {
                'id_usuario': id_usuario,
                'monto': round(random.uniform(500, 2000), 2),
                'moneda': 'USD',
                'comercio': comercio['nombre'],
                'ciudad': ubicacion['ciudad'],
                'pais': ubicacion['pais'],
                'mcc': comercio['mcc']
            }
        
        elif tipo_fraude == 'categoria_riesgo':
            # Categoría de alto riesgo
            ubicacion = random.choice(self.ciudades_mexico)
            comercio = random.choice(self.comercios_riesgo)
            transaccion = {
                'id_usuario': id_usuario,
                'monto': round(random.uniform(1000, 5000), 2),
                'moneda': 'MXN',
                'comercio': comercio['nombre'],
                'ciudad': ubicacion['ciudad'],
                'pais': ubicacion['pais'],
                'mcc': comercio['mcc']
            }
        
        else:  # combinado
            # Múltiples factores de riesgo
            ubicacion = random.choice(self.ciudades_internacionales)
            comercio = random.choice(self.comercios_riesgo)
            transaccion = {
                'id_usuario': id_usuario,
                'monto': round(random.uniform(8000, 20000), 2),
                'moneda': 'USD',
                'comercio': comercio['nombre'],
                'ciudad': ubicacion['ciudad'],
                'pais': ubicacion['pais'],
                'mcc': comercio['mcc']
            }
        
        return transaccion
    
    def generar_historial_usuario(self, id_usuario, num_transacciones=30, probabilidad_fraude=0.1, ciudad_base='CDMX'):
        """
        Genera un historial de transacciones para un usuario
        
        Args:
            id_usuario (str): UUID del usuario
            num_transacciones (int): Número de transacciones a generar
            probabilidad_fraude (float): Probabilidad de generar transacción fraudulenta (0.0-1.0)
            ciudad_base (str): Ciudad base del usuario
        """
        print(f"\n{'='*60}")
        print(f"Generando historial para usuario: {id_usuario[:8]}...")
        print(f"Ciudad base: {ciudad_base}")
        print(f"Transacciones a generar: {num_transacciones}")
        print(f"{'='*60}\n")
        
        self.db.connect()
        
        transacciones_exitosas = 0
        transacciones_fraudulentas = 0
        
        for i in range(num_transacciones):
            # Decidir si es fraudulenta
            if random.random() < probabilidad_fraude:
                transaccion = self.generar_transaccion_fraudulenta(id_usuario)
                tipo = "FRAUDE"
                transacciones_fraudulentas += 1
            else:
                transaccion = self.generar_transaccion_normal(id_usuario, ciudad_base)
                tipo = "NORMAL"
            
            resultado = self.db.insertar_transaccion(transaccion)
            
            if resultado['success']:
                transacciones_exitosas += 1
                print(f"  ✓ [{i+1}/{num_transacciones}] {tipo:7} | ${transaccion['monto']:>8.2f} {transaccion['moneda']} | {transaccion['comercio'][:30]:<30} | {transaccion['ciudad']}")
            else:
                print(f"  ✗ [{i+1}/{num_transacciones}] ERROR: {resultado.get('error', 'Unknown')}")
        
        self.db.disconnect()
        
        print(f"\n{'='*60}")
        print(f"✓ Historial generado exitosamente")
        print(f"  Transacciones creadas: {transacciones_exitosas}/{num_transacciones}")
        print(f"  Transacciones normales: {transacciones_exitosas - transacciones_fraudulentas}")
        print(f"  Transacciones fraudulentas: {transacciones_fraudulentas}")
        print(f"{'='*60}\n")


def main():
    """
    Script principal para generar datos de prueba
    """
    print("\n" + "="*60)
    print("GENERADOR DE DATOS DE PRUEBA")
    print("Sistema de Detección de Fraude")
    print("="*60 + "\n")
    
    generator = DataGenerator()
    
    # Generar 3 usuarios de prueba
    usuarios = [
        {
            'id': str(uuid.uuid4()),
            'ciudad_base': 'CDMX',
            'num_transacciones': 40,
            'prob_fraude': 0.1
        },
        {
            'id': str(uuid.uuid4()),
            'ciudad_base': 'Guadalajara',
            'num_transacciones': 35,
            'prob_fraude': 0.15
        },
        {
            'id': str(uuid.uuid4()),
            'ciudad_base': 'Monterrey',
            'num_transacciones': 30,
            'prob_fraude': 0.05
        }
    ]
    
    print("USUARIOS GENERADOS:\n")
    for i, user in enumerate(usuarios, 1):
        print(f"  Usuario {i}:")
        print(f"    ID: {user['id']}")
        print(f"    Ciudad base: {user['ciudad_base']}")
        print(f"    Transacciones: {user['num_transacciones']}")
        print(f"    Prob. fraude: {user['prob_fraude']*100}%")
        print()
    
    input("\nPresiona ENTER para comenzar a generar datos...")
    
    # Generar historial para cada usuario
    for user in usuarios:
        generator.generar_historial_usuario(
            id_usuario=user['id'],
            num_transacciones=user['num_transacciones'],
            probabilidad_fraude=user['prob_fraude'],
            ciudad_base=user['ciudad_base']
        )
    
    print("\n" + "="*60)
    print("✓ GENERACIÓN DE DATOS COMPLETADA")
    print("="*60)
    print("\nGUARDA ESTOS IDs PARA HACER PRUEBAS:\n")
    for i, user in enumerate(usuarios, 1):
        print(f"  Usuario {i}: {user['id']}")
    print()


if __name__ == "__main__":
    main()
