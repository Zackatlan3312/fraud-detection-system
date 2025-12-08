#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Exploración de Cassandra
Sistema de Detección de Fraude

Uso:
    python explorar_cassandra.py
"""

import os
os.environ['CASS_DRIVER_NO_CYTHON'] = '1'
os.environ['CASS_DRIVER_NO_EXTENSIONS'] = '1'

from cassandra.cluster import Cluster
from datetime import datetime
import uuid

class ExploradorCassandra:
    def __init__(self):
        self.cluster = None
        self.session = None
    
    def conectar(self):
        """Conectar a Cassandra"""
        try:
            print("🔌 Conectando a Cassandra...")
            self.cluster = Cluster(['127.0.0.1'], port=9042)
            self.session = self.cluster.connect()
            self.session.set_keyspace('finanzas')
            print("✅ Conectado exitosamente!\n")
            return True
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            return False
    
    def desconectar(self):
        """Desconectar de Cassandra"""
        if self.cluster:
            self.cluster.shutdown()
            print("\n🔌 Desconectado de Cassandra")
    
    def mostrar_menu(self):
        """Mostrar menú de opciones"""
        print("\n" + "="*60)
        print("🗄️  EXPLORADOR DE CASSANDRA - Sistema de Detección de Fraude")
        print("="*60)
        print("\n📊 CONSULTAS BÁSICAS:")
        print("  1. Ver todos los keyspaces")
        print("  2. Ver todas las tablas del keyspace 'finanzas'")
        print("  3. Ver estructura de tabla 'transacciones_por_usuario'")
        print("  4. Ver estructura de tabla 'transacciones_por_id'")
        
        print("\n👤 CONSULTAS DE USUARIOS:")
        print("  5. Listar todos los usuarios con transacciones")
        print("  6. Ver transacciones de un usuario específico")
        print("  7. Ver estadísticas de un usuario")
        
        print("\n💰 CONSULTAS DE TRANSACCIONES:")
        print("  8. Ver últimas 10 transacciones (todos los usuarios)")
        print("  9. Buscar transacción por ID")
        print(" 10. Ver transacciones por ciudad")
        print(" 11. Ver transacciones por monto (mayor a X)")
        
        print("\n📈 ESTADÍSTICAS:")
        print(" 12. Contar total de transacciones")
        print(" 13. Ver distribución por país")
        print(" 14. Ver comercios más frecuentes")
        print(" 15. Ver categorías (MCC) más usadas")
        
        print("\n🔧 AVANZADO:")
        print(" 16. Ejecutar query personalizada")
        print(" 17. Ver información del cluster")
        
        print("\n  0. Salir")
        print("="*60)
    
    # ============================================
    # CONSULTAS BÁSICAS
    # ============================================
    
    def ver_keyspaces(self):
        """Ver todos los keyspaces"""
        print("\n📂 KEYSPACES EN CASSANDRA:")
        print("-" * 60)
        
        query = "SELECT keyspace_name FROM system_schema.keyspaces"
        rows = self.session.execute(query)
        
        for i, row in enumerate(rows, 1):
            print(f"  {i}. {row.keyspace_name}")
    
    def ver_tablas(self):
        """Ver todas las tablas del keyspace finanzas"""
        print("\n📋 TABLAS EN KEYSPACE 'finanzas':")
        print("-" * 60)
        
        query = """
            SELECT table_name 
            FROM system_schema.tables 
            WHERE keyspace_name = 'finanzas'
        """
        rows = self.session.execute(query)
        
        for i, row in enumerate(rows, 1):
            print(f"  {i}. {row.table_name}")
    
    def ver_estructura_tabla(self, tabla):
        """Ver estructura de una tabla"""
        print(f"\n🏗️  ESTRUCTURA DE TABLA '{tabla}':")
        print("-" * 60)
        
        query = f"DESCRIBE TABLE {tabla}"
        try:
            # En Python driver, usamos una query diferente
            query = """
                SELECT column_name, type, kind 
                FROM system_schema.columns 
                WHERE keyspace_name = 'finanzas' 
                AND table_name = %s
            """
            rows = self.session.execute(query, (tabla,))
            
            print(f"\n{'Columna':<25} {'Tipo':<20} {'Kind':<15}")
            print("-" * 60)
            for row in rows:
                print(f"{row.column_name:<25} {row.type:<20} {row.kind:<15}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # ============================================
    # CONSULTAS DE USUARIOS
    # ============================================
    
    def listar_usuarios(self):
        """Listar todos los usuarios con transacciones"""
        print("\n👥 USUARIOS CON TRANSACCIONES:")
        print("-" * 60)
        
        query = "SELECT DISTINCT id_usuario FROM transacciones_por_usuario LIMIT 100"
        rows = self.session.execute(query)
        
        usuarios = list(rows)
        if not usuarios:
            print("  ⚠️  No hay usuarios en la base de datos")
            return
        
        for i, row in enumerate(usuarios, 1):
            print(f"  {i}. {row.id_usuario}")
        
        print(f"\n  📊 Total: {len(usuarios)} usuarios")
    
    def ver_transacciones_usuario(self):
        """Ver transacciones de un usuario específico"""
        print("\n💳 TRANSACCIONES DE USUARIO:")
        print("-" * 60)
        
        # Primero, listar usuarios disponibles
        query = "SELECT DISTINCT id_usuario FROM transacciones_por_usuario LIMIT 10"
        rows = self.session.execute(query)
        usuarios = list(rows)
        
        if not usuarios:
            print("  ⚠️  No hay usuarios en la base de datos")
            return
        
        print("\n📋 Usuarios disponibles:")
        for i, row in enumerate(usuarios, 1):
            print(f"  {i}. {row.id_usuario}")
        
        try:
            opcion = int(input("\n👉 Selecciona un usuario (número): "))
            if 1 <= opcion <= len(usuarios):
                id_usuario = usuarios[opcion - 1].id_usuario
                
                limite = int(input("👉 ¿Cuántas transacciones ver? (default 10): ") or "10")
                
                # Obtener transacciones
                query = """
                    SELECT timestamp, monto, moneda, comercio, ciudad, pais, mcc
                    FROM transacciones_por_usuario
                    WHERE id_usuario = %s
                    LIMIT %s
                """
                rows = self.session.execute(query, (id_usuario, limite))
                
                print(f"\n📊 Últimas {limite} transacciones de: {id_usuario}")
                print("-" * 100)
                print(f"{'Fecha':<20} {'Monto':<12} {'Moneda':<8} {'Comercio':<25} {'Ciudad':<15} {'País':<15}")
                print("-" * 100)
                
                for row in rows:
                    fecha = row.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{fecha:<20} {row.monto:<12.2f} {row.moneda:<8} {row.comercio:<25} {row.ciudad:<15} {row.pais:<15}")
            else:
                print("❌ Opción inválida")
        except ValueError:
            print("❌ Entrada inválida")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def ver_estadisticas_usuario(self):
        """Ver estadísticas de un usuario"""
        print("\n📊 ESTADÍSTICAS DE USUARIO:")
        print("-" * 60)
        
        # Listar usuarios
        query = "SELECT DISTINCT id_usuario FROM transacciones_por_usuario LIMIT 10"
        rows = self.session.execute(query)
        usuarios = list(rows)
        
        if not usuarios:
            print("  ⚠️  No hay usuarios en la base de datos")
            return
        
        print("\n📋 Usuarios disponibles:")
        for i, row in enumerate(usuarios, 1):
            print(f"  {i}. {row.id_usuario}")
        
        try:
            opcion = int(input("\n👉 Selecciona un usuario (número): "))
            if 1 <= opcion <= len(usuarios):
                id_usuario = usuarios[opcion - 1].id_usuario
                
                # Obtener todas las transacciones
                query = """
                    SELECT monto, ciudad, comercio, mcc
                    FROM transacciones_por_usuario
                    WHERE id_usuario = %s
                """
                rows = self.session.execute(query, (id_usuario,))
                transacciones = list(rows)
                
                if not transacciones:
                    print("  ⚠️  Este usuario no tiene transacciones")
                    return
                
                # Calcular estadísticas
                total_tx = len(transacciones)
                montos = [float(t.monto) for t in transacciones]
                monto_total = sum(montos)
                monto_promedio = monto_total / total_tx
                monto_max = max(montos)
                monto_min = min(montos)
                
                ciudades = {}
                comercios = {}
                mccs = {}
                
                for t in transacciones:
                    ciudades[t.ciudad] = ciudades.get(t.ciudad, 0) + 1
                    comercios[t.comercio] = comercios.get(t.comercio, 0) + 1
                    mccs[t.mcc] = mccs.get(t.mcc, 0) + 1
                
                # Mostrar estadísticas
                print(f"\n📈 ESTADÍSTICAS DE USUARIO: {id_usuario}")
                print("=" * 60)
                print(f"\n💰 MONTOS:")
                print(f"  Total transacciones: {total_tx}")
                print(f"  Monto total: ${monto_total:,.2f}")
                print(f"  Monto promedio: ${monto_promedio:,.2f}")
                print(f"  Monto máximo: ${monto_max:,.2f}")
                print(f"  Monto mínimo: ${monto_min:,.2f}")
                
                print(f"\n🌍 CIUDADES MÁS FRECUENTES:")
                for ciudad, count in sorted(ciudades.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"  {ciudad}: {count} transacciones")
                
                print(f"\n🏪 COMERCIOS MÁS FRECUENTES:")
                for comercio, count in sorted(comercios.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"  {comercio}: {count} transacciones")
                
                print(f"\n🏷️  CATEGORÍAS (MCC) MÁS USADAS:")
                for mcc, count in sorted(mccs.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"  MCC {mcc}: {count} transacciones")
            else:
                print("❌ Opción inválida")
        except ValueError:
            print("❌ Entrada inválida")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # ============================================
    # CONSULTAS DE TRANSACCIONES
    # ============================================
    
    def ver_ultimas_transacciones(self):
        """Ver últimas transacciones de todos los usuarios"""
        print("\n💳 ÚLTIMAS 10 TRANSACCIONES (TODOS LOS USUARIOS):")
        print("-" * 100)
        
        # Nota: En Cassandra esto requiere ALLOW FILTERING y es ineficiente
        # Para demo, tomamos de un usuario específico
        query = """
            SELECT id_usuario, timestamp, monto, moneda, comercio, ciudad
            FROM transacciones_por_usuario
            LIMIT 10
        """
        
        try:
            rows = self.session.execute(query)
            
            print(f"{'Usuario (primeros 8)':<20} {'Fecha':<20} {'Monto':<12} {'Comercio':<25} {'Ciudad':<15}")
            print("-" * 100)
            
            for row in rows:
                usuario_corto = str(row.id_usuario)[:8]
                fecha = row.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                print(f"{usuario_corto:<20} {fecha:<20} ${row.monto:<11.2f} {row.comercio:<25} {row.ciudad:<15}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def buscar_transaccion_por_id(self):
        """Buscar una transacción por su ID"""
        print("\n🔍 BUSCAR TRANSACCIÓN POR ID:")
        print("-" * 60)
        
        id_tx = input("👉 Ingresa el ID de la transacción (UUID): ").strip()
        
        try:
            id_tx_uuid = uuid.UUID(id_tx)
            
            query = """
                SELECT *
                FROM transacciones_por_id
                WHERE id_transaccion = %s
            """
            row = self.session.execute(query, (id_tx_uuid,)).one()
            
            if row:
                print(f"\n✅ Transacción encontrada:")
                print("-" * 60)
                print(f"  ID Transacción: {row.id_transaccion}")
                print(f"  Usuario: {row.id_usuario}")
                print(f"  Fecha: {row.timestamp}")
                print(f"  Monto: ${row.monto} {row.moneda}")
                print(f"  Comercio: {row.comercio}")
                print(f"  Ubicación: {row.ciudad}, {row.pais}")
                print(f"  MCC: {row.mcc}")
            else:
                print("❌ Transacción no encontrada")
        except ValueError:
            print("❌ ID inválido (debe ser un UUID)")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def ver_transacciones_por_ciudad(self):
        """Ver transacciones por ciudad"""
        print("\n🌍 TRANSACCIONES POR CIUDAD:")
        print("-" * 60)
        
        ciudad = input("👉 Ingresa el nombre de la ciudad: ").strip()
        
        # Nota: Esto requiere ALLOW FILTERING en producción
        print(f"\n⚠️  Nota: Esta query es ineficiente en producción")
        print(f"    En un sistema real, crearíamos una tabla específica para esta consulta")
        
        try:
            query = """
                SELECT id_usuario, timestamp, monto, comercio
                FROM transacciones_por_usuario
                WHERE ciudad = %s
                ALLOW FILTERING
                LIMIT 20
            """
            rows = self.session.execute(query, (ciudad,))
            
            transacciones = list(rows)
            if not transacciones:
                print(f"\n❌ No se encontraron transacciones en {ciudad}")
                return
            
            print(f"\n📊 Transacciones en {ciudad}:")
            print("-" * 80)
            print(f"{'Usuario (8 dígitos)':<20} {'Fecha':<20} {'Monto':<12} {'Comercio':<25}")
            print("-" * 80)
            
            for row in transacciones:
                usuario_corto = str(row.id_usuario)[:8]
                fecha = row.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                print(f"{usuario_corto:<20} {fecha:<20} ${row.monto:<11.2f} {row.comercio:<25}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def ver_transacciones_por_monto(self):
        """Ver transacciones mayores a un monto"""
        print("\n💵 TRANSACCIONES POR MONTO:")
        print("-" * 60)
        
        try:
            monto_min = float(input("👉 Monto mínimo: $"))
            
            print(f"\n⚠️  Nota: Esta query es ineficiente en producción")
            print(f"    Cassandra no está optimizado para filtros por valores numéricos")
            
            query = """
                SELECT id_usuario, timestamp, monto, moneda, comercio, ciudad
                FROM transacciones_por_usuario
                WHERE monto > %s
                ALLOW FILTERING
                LIMIT 20
            """
            rows = self.session.execute(query, (monto_min,))
            
            transacciones = list(rows)
            if not transacciones:
                print(f"\n❌ No se encontraron transacciones mayores a ${monto_min}")
                return
            
            print(f"\n📊 Transacciones > ${monto_min}:")
            print("-" * 100)
            print(f"{'Usuario (8 dígitos)':<20} {'Fecha':<20} {'Monto':<12} {'Comercio':<25} {'Ciudad':<15}")
            print("-" * 100)
            
            for row in transacciones:
                usuario_corto = str(row.id_usuario)[:8]
                fecha = row.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                print(f"{usuario_corto:<20} {fecha:<20} ${row.monto:<11.2f} {row.comercio:<25} {row.ciudad:<15}")
        except ValueError:
            print("❌ Monto inválido")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # ============================================
    # ESTADÍSTICAS
    # ============================================
    
    def contar_transacciones(self):
        """Contar total de transacciones"""
        print("\n🔢 TOTAL DE TRANSACCIONES:")
        print("-" * 60)
        
        try:
            query = "SELECT COUNT(*) FROM transacciones_por_usuario"
            row = self.session.execute(query).one()
            
            print(f"\n  📊 Total: {row.count:,} transacciones")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def ver_distribucion_pais(self):
        """Ver distribución de transacciones por país"""
        print("\n🌍 DISTRIBUCIÓN POR PAÍS:")
        print("-" * 60)
        
        try:
            query = "SELECT pais FROM transacciones_por_usuario"
            rows = self.session.execute(query)
            
            paises = {}
            total = 0
            for row in rows:
                paises[row.pais] = paises.get(row.pais, 0) + 1
                total += 1
            
            print(f"\n{'País':<20} {'Transacciones':<15} {'Porcentaje':<10}")
            print("-" * 50)
            
            for pais, count in sorted(paises.items(), key=lambda x: x[1], reverse=True):
                porcentaje = (count / total) * 100
                print(f"{pais:<20} {count:<15} {porcentaje:>6.2f}%")
            
            print("-" * 50)
            print(f"{'TOTAL':<20} {total:<15} {100.0:>6.2f}%")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def ver_comercios_frecuentes(self):
        """Ver comercios más frecuentes"""
        print("\n🏪 COMERCIOS MÁS FRECUENTES:")
        print("-" * 60)
        
        try:
            query = "SELECT comercio FROM transacciones_por_usuario"
            rows = self.session.execute(query)
            
            comercios = {}
            for row in rows:
                comercios[row.comercio] = comercios.get(row.comercio, 0) + 1
            
            print(f"\n{'Comercio':<30} {'Transacciones':<15}")
            print("-" * 50)
            
            for comercio, count in sorted(comercios.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"{comercio:<30} {count:<15}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def ver_categorias_frecuentes(self):
        """Ver categorías MCC más usadas"""
        print("\n🏷️  CATEGORÍAS (MCC) MÁS USADAS:")
        print("-" * 60)
        
        # Diccionario de MCCs
        mcc_nombres = {
            5411: "Supermercados",
            5812: "Restaurantes",
            5814: "Cafeterías",
            5541: "Gasolineras",
            5999: "Comercio en línea",
            7995: "Casinos/Apuestas",
            4899: "Streaming",
        }
        
        try:
            query = "SELECT mcc FROM transacciones_por_usuario"
            rows = self.session.execute(query)
            
            mccs = {}
            for row in rows:
                mccs[row.mcc] = mccs.get(row.mcc, 0) + 1
            
            print(f"\n{'MCC':<8} {'Descripción':<25} {'Transacciones':<15}")
            print("-" * 55)
            
            for mcc, count in sorted(mccs.items(), key=lambda x: x[1], reverse=True):
                descripcion = mcc_nombres.get(mcc, "Desconocido")
                print(f"{mcc:<8} {descripcion:<25} {count:<15}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # ============================================
    # AVANZADO
    # ============================================
    
    def ejecutar_query_personalizada(self):
        """Ejecutar una query CQL personalizada"""
        print("\n⚙️  EJECUTAR QUERY PERSONALIZADA:")
        print("-" * 60)
        print("⚠️  Cuidado: Queries mal formadas pueden causar errores")
        print("Ejemplo: SELECT * FROM transacciones_por_usuario LIMIT 5")
        
        query = input("\n👉 Ingresa tu query CQL: ").strip()
        
        if not query:
            print("❌ Query vacía")
            return
        
        try:
            rows = self.session.execute(query)
            
            # Convertir a lista para poder contar
            resultados = list(rows)
            
            if not resultados:
                print("\n✅ Query ejecutada (0 resultados)")
                return
            
            print(f"\n✅ Query ejecutada ({len(resultados)} resultados):")
            print("-" * 100)
            
            # Mostrar primeros 20 resultados
            for i, row in enumerate(resultados[:20], 1):
                print(f"\n  Fila {i}:")
                for col in row._fields:
                    valor = getattr(row, col)
                    print(f"    {col}: {valor}")
            
            if len(resultados) > 20:
                print(f"\n  ... y {len(resultados) - 20} resultados más")
        except Exception as e:
            print(f"❌ Error ejecutando query: {e}")
    
    def ver_info_cluster(self):
        """Ver información del cluster de Cassandra"""
        print("\n🖥️  INFORMACIÓN DEL CLUSTER:")
        print("-" * 60)
        
        try:
            # Información del keyspace
            query = """
                SELECT replication
                FROM system_schema.keyspaces
                WHERE keyspace_name = 'finanzas'
            """
            row = self.session.execute(query).one()
            
            print(f"\n📊 Keyspace 'finanzas':")
            print(f"  Estrategia de replicación: {row.replication}")
            
            # Información de las tablas
            query = """
                SELECT table_name
                FROM system_schema.tables
                WHERE keyspace_name = 'finanzas'
            """
            rows = self.session.execute(query)
            
            print(f"\n📋 Tablas:")
            for row in rows:
                print(f"  - {row.table_name}")
            
            # Información del cluster
            print(f"\n🌐 Cluster:")
            print(f"  Nombre: {self.cluster.metadata.cluster_name}")
            print(f"  Partitioner: {self.cluster.metadata.partitioner}")
            
            # Nodos
            print(f"\n🖥️  Nodos:")
            for host in self.cluster.metadata.all_hosts():
                print(f"  - {host.address} (Datacenter: {host.datacenter}, Rack: {host.rack})")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # ============================================
    # MAIN LOOP
    # ============================================
    
    def ejecutar(self):
        """Ejecutar el explorador"""
        if not self.conectar():
            return
        
        while True:
            self.mostrar_menu()
            
            try:
                opcion = input("\n👉 Selecciona una opción: ").strip()
                
                if opcion == "0":
                    print("\n👋 ¡Hasta luego!")
                    break
                elif opcion == "1":
                    self.ver_keyspaces()
                elif opcion == "2":
                    self.ver_tablas()
                elif opcion == "3":
                    self.ver_estructura_tabla("transacciones_por_usuario")
                elif opcion == "4":
                    self.ver_estructura_tabla("transacciones_por_id")
                elif opcion == "5":
                    self.listar_usuarios()
                elif opcion == "6":
                    self.ver_transacciones_usuario()
                elif opcion == "7":
                    self.ver_estadisticas_usuario()
                elif opcion == "8":
                    self.ver_ultimas_transacciones()
                elif opcion == "9":
                    self.buscar_transaccion_por_id()
                elif opcion == "10":
                    self.ver_transacciones_por_ciudad()
                elif opcion == "11":
                    self.ver_transacciones_por_monto()
                elif opcion == "12":
                    self.contar_transacciones()
                elif opcion == "13":
                    self.ver_distribucion_pais()
                elif opcion == "14":
                    self.ver_comercios_frecuentes()
                elif opcion == "15":
                    self.ver_categorias_frecuentes()
                elif opcion == "16":
                    self.ejecutar_query_personalizada()
                elif opcion == "17":
                    self.ver_info_cluster()
                else:
                    print("\n❌ Opción inválida. Intenta de nuevo.")
                
                input("\n⏸️  Presiona Enter para continuar...")
            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                input("\n⏸️  Presiona Enter para continuar...")
        
        self.desconectar()


if __name__ == "__main__":
    explorador = ExploradorCassandra()
    explorador.ejecutar()
