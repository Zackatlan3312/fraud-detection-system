# 📊 GUÍA DE CONSULTAS CQL - CASSANDRA

## 🎯 CONSULTAS PARA TU PRESENTACIÓN

Esta guía contiene todas las consultas útiles que puedes mostrar durante tu presentación.

---

## 🔌 CONECTAR A CASSANDRA

### **Desde Terminal:**

```bash
# Conectar al contenedor de Cassandra
docker exec -it cassandra-fraud cqlsh

# Deberías ver:
# cqlsh>
```

### **Usar el keyspace:**

```cql
USE finanzas;
```

---

## 📋 CONSULTAS BÁSICAS

### 1. Ver todos los keyspaces

```cql
SELECT keyspace_name FROM system_schema.keyspaces;
```

**Resultado esperado:**
```
 keyspace_name
----------------
 system_auth
 system_schema
 system_distributed
 system
 finanzas         ← NUESTRO KEYSPACE
```

---

### 2. Ver todas las tablas de 'finanzas'

```cql
DESCRIBE TABLES;
```

**Resultado esperado:**
```
transacciones_por_usuario  transacciones_por_id
```

---

### 3. Ver estructura de tabla

```cql
DESCRIBE TABLE transacciones_por_usuario;
```

**Resultado esperado:**
```cql
CREATE TABLE finanzas.transacciones_por_usuario (
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
) WITH CLUSTERING ORDER BY (timestamp DESC);
```

---

## 👥 CONSULTAS DE USUARIOS

### 4. Listar usuarios con transacciones

```cql
SELECT DISTINCT id_usuario 
FROM transacciones_por_usuario 
LIMIT 10;
```

**Para qué sirve:** Ver qué usuarios tienen transacciones en el sistema.

---

### 5. Ver transacciones de un usuario específico

```cql
SELECT timestamp, monto, moneda, comercio, ciudad, pais
FROM transacciones_por_usuario
WHERE id_usuario = 550e8400-e29b-41d4-a716-446655440000
LIMIT 10;
```

**Para qué sirve:** Obtener el historial de un usuario (usado en detección de fraude).

**⚡ Velocidad:** ~5ms (gracias a la partition key)

---

### 6. Contar transacciones de un usuario

```cql
SELECT COUNT(*)
FROM transacciones_por_usuario
WHERE id_usuario = 550e8400-e29b-41d4-a716-446655440000;
```

---

## 💰 CONSULTAS DE TRANSACCIONES

### 7. Buscar transacción por ID

```cql
SELECT *
FROM transacciones_por_id
WHERE id_transaccion = 6ba7b810-9dad-11d1-80b4-00c04fd430c8;
```

**Para qué sirve:** Buscar detalles de una transacción específica.

**⚡ Velocidad:** ~2ms (lookup directo)

---

### 8. Ver últimas transacciones (limitado)

```cql
SELECT id_usuario, timestamp, monto, comercio, ciudad
FROM transacciones_por_usuario
LIMIT 20;
```

**⚠️ Nota:** En Cassandra, las queries sin partition key son ineficientes. Esta query escanea múltiples particiones.

---

### 9. Ver transacciones en un rango de fechas

```cql
SELECT timestamp, monto, comercio
FROM transacciones_por_usuario
WHERE id_usuario = 550e8400-e29b-41d4-a716-446655440000
  AND timestamp >= '2025-12-01 00:00:00'
  AND timestamp <= '2025-12-08 23:59:59';
```

**Para qué sirve:** Análisis temporal de transacciones.

---

## 📊 ESTADÍSTICAS (Para Demo)

### 10. Contar total de transacciones

```cql
SELECT COUNT(*)
FROM transacciones_por_usuario;
```

**⚠️ Advertencia:** Esta query es lenta en tablas grandes (escanea todas las particiones).

---

### 11. Ver distribución por país

```cql
SELECT pais, COUNT(*)
FROM transacciones_por_usuario
GROUP BY pais
ALLOW FILTERING;
```

**⚠️ Nota:** `ALLOW FILTERING` es ineficiente. En producción, crearíamos una tabla específica para esta query.

---

### 12. Ver transacciones de una ciudad específica

```cql
SELECT id_usuario, timestamp, monto, comercio
FROM transacciones_por_usuario
WHERE ciudad = 'CDMX'
ALLOW FILTERING
LIMIT 20;
```

**⚠️ Nota:** Esta query es ineficiente. En un sistema real, crearíamos:
- Una tabla `transacciones_por_ciudad` con `ciudad` como partition key

---

### 13. Ver transacciones mayores a un monto

```cql
SELECT id_usuario, timestamp, monto, comercio
FROM transacciones_por_usuario
WHERE monto > 1000
ALLOW FILTERING
LIMIT 20;
```

**⚠️ Problema:** Cassandra no está optimizado para filtros numéricos.

**Solución en producción:** Usar una tabla materializada o procesar en la aplicación.

---

## 🔧 CONSULTAS AVANZADAS

### 14. Insertar una transacción manualmente

```cql
INSERT INTO transacciones_por_usuario (
    id_usuario, 
    timestamp, 
    id_transaccion,
    monto, 
    moneda, 
    comercio, 
    ciudad, 
    pais, 
    mcc
) VALUES (
    550e8400-e29b-41d4-a716-446655440000,
    '2025-12-08 10:30:00',
    now(),
    250.50,
    'MXN',
    'Oxxo',
    'CDMX',
    'Mexico',
    5411
);
```

---

### 15. Actualizar una transacción

```cql
UPDATE transacciones_por_usuario
SET monto = 300.00
WHERE id_usuario = 550e8400-e29b-41d4-a716-446655440000
  AND timestamp = '2025-12-08 10:30:00'
  AND id_transaccion = 6ba7b810-9dad-11d1-80b4-00c04fd430c8;
```

**⚠️ Importante:** En Cassandra, necesitas especificar TODA la PRIMARY KEY para actualizar.

---

### 16. Eliminar una transacción

```cql
DELETE FROM transacciones_por_usuario
WHERE id_usuario = 550e8400-e29b-41d4-a716-446655440000
  AND timestamp = '2025-12-08 10:30:00'
  AND id_transaccion = 6ba7b810-9dad-11d1-80b4-00c04fd430c8;
```

---

### 17. Truncar tabla (eliminar todos los datos)

```cql
TRUNCATE transacciones_por_usuario;
```

**⚠️ CUIDADO:** Esto elimina TODOS los datos de la tabla.

---

## 🗄️ INFORMACIÓN DEL SISTEMA

### 18. Ver información del keyspace

```cql
SELECT *
FROM system_schema.keyspaces
WHERE keyspace_name = 'finanzas';
```

---

### 19. Ver información de columnas de una tabla

```cql
SELECT column_name, type, kind
FROM system_schema.columns
WHERE keyspace_name = 'finanzas'
  AND table_name = 'transacciones_por_usuario';
```

**Resultado:**
```
 column_name    | type      | kind
----------------+-----------+-----------
 id_usuario     | uuid      | partition_key
 timestamp      | timestamp | clustering
 id_transaccion | timeuuid  | clustering
 monto          | decimal   | regular
 moneda         | text      | regular
 ...
```

---

### 20. Ver nodos del cluster

```cql
SELECT peer, data_center, rack, release_version
FROM system.peers;
```

---

## ⚠️ QUERIES INEFICIENTES (Evitar en Producción)

### ❌ Query sin partition key

```cql
-- MALO: Escanea TODAS las particiones
SELECT *
FROM transacciones_por_usuario
WHERE monto > 1000
ALLOW FILTERING;
```

**Problema:** Complejidad O(n) - muy lento con millones de filas.

**Solución:** Crear una tabla específica para esta query.

---

### ❌ Query con Secondary Index en columna de alta cardinalidad

```cql
-- MALO: Secondary index ineficiente
CREATE INDEX ON transacciones_por_usuario(id_transaccion);

SELECT *
FROM transacciones_por_usuario
WHERE id_transaccion = ?;
```

**Problema:** Los secondary indexes son lentos en Cassandra.

**Solución:** Ya tenemos `transacciones_por_id` para esto.

---

## ✅ QUERIES EFICIENTES (Usar en Producción)

### ✅ Query con partition key

```cql
-- BUENO: Lookup directo a una partición
SELECT *
FROM transacciones_por_usuario
WHERE id_usuario = ?
LIMIT 50;
```

**Complejidad:** O(1) - ~5ms

---

### ✅ Query con partition + clustering keys

```cql
-- BUENO: Rango dentro de una partición
SELECT *
FROM transacciones_por_usuario
WHERE id_usuario = ?
  AND timestamp > '2025-12-01'
  AND timestamp < '2025-12-08';
```

**Complejidad:** O(log n) - ~10ms

---

## 🎯 QUERIES PARA MOSTRAR EN LA PRESENTACIÓN

### **Demo 1: Mostrar estructura de datos**

```cql
USE finanzas;
DESCRIBE TABLES;
DESCRIBE TABLE transacciones_por_usuario;
```

**Explicar:**
- Partition key: `id_usuario`
- Clustering keys: `timestamp, id_transaccion`
- Datos ordenados automáticamente

---

### **Demo 2: Listar usuarios**

```cql
SELECT DISTINCT id_usuario 
FROM transacciones_por_usuario 
LIMIT 5;
```

**Explicar:** Estos son los usuarios con transacciones en el sistema.

---

### **Demo 3: Ver historial de un usuario (RÁPIDO)**

```cql
SELECT timestamp, monto, moneda, comercio, ciudad
FROM transacciones_por_usuario
WHERE id_usuario = [COPIAR UN UUID DE LA QUERY ANTERIOR]
LIMIT 10;
```

**Explicar:** 
- Query en ~5ms
- Gracias a partition key
- Datos ya ordenados por timestamp

---

### **Demo 4: Buscar transacción por ID (RÁPIDO)**

```cql
-- Primero, copiar un id_transaccion de la query anterior
SELECT *
FROM transacciones_por_id
WHERE id_transaccion = [COPIAR UN TIMEUUID];
```

**Explicar:**
- Lookup directo
- ~2ms
- Por eso tenemos dos tablas

---

### **Demo 5: Contar transacciones**

```cql
SELECT COUNT(*)
FROM transacciones_por_usuario;
```

**Explicar:** Tenemos [X] transacciones en el sistema.

---

### **Demo 6: Query ineficiente (mostrar ALLOW FILTERING)**

```cql
SELECT id_usuario, monto, comercio
FROM transacciones_por_usuario
WHERE monto > 1000
ALLOW FILTERING
LIMIT 10;
```

**Explicar:**
- `ALLOW FILTERING` = query ineficiente
- Escanea todas las particiones
- En producción, evitar esto
- Solución: crear tabla específica

---

## 📝 SCRIPT COMPLETO PARA DEMO

```cql
-- 1. Conectar
USE finanzas;

-- 2. Ver estructura
DESCRIBE TABLES;
DESCRIBE TABLE transacciones_por_usuario;

-- 3. Listar usuarios
SELECT DISTINCT id_usuario FROM transacciones_por_usuario LIMIT 5;

-- 4. Ver transacciones de un usuario (COPIAR UUID DE ARRIBA)
SELECT timestamp, monto, moneda, comercio, ciudad
FROM transacciones_por_usuario
WHERE id_usuario = 550e8400-e29b-41d4-a716-446655440000
LIMIT 10;

-- 5. Contar transacciones
SELECT COUNT(*) FROM transacciones_por_usuario;

-- 6. Ver distribución por país
SELECT pais, COUNT(*) FROM transacciones_por_usuario GROUP BY pais ALLOW FILTERING;

-- 7. Buscar por ID (COPIAR UN ID_TRANSACCION DE LA QUERY 4)
SELECT * FROM transacciones_por_id WHERE id_transaccion = 6ba7b810-9dad-11d1-80b4-00c04fd430c8;

-- 8. Mostrar query ineficiente
SELECT * FROM transacciones_por_usuario WHERE monto > 1000 ALLOW FILTERING LIMIT 10;
```

---

## 🚀 CÓMO USAR EN TU PRESENTACIÓN

### **Opción 1: Terminal CQL**

```bash
docker exec -it cassandra-fraud cqlsh
```

Luego ejecuta las queries de arriba.

### **Opción 2: Script Python**

```bash
python explorar_cassandra.py
```

Menú interactivo con todas las consultas.

### **Opción 3: Mostrar en slides**

Incluye capturas de pantalla de las queries en tu presentación.

---

## 💡 PUNTOS CLAVE PARA EXPLICAR

1. **Partition Key** determina en qué nodo se almacenan los datos
2. **Clustering Keys** definen el orden dentro de la partición
3. **Queries eficientes** usan partition key
4. **ALLOW FILTERING** = ineficiente, evitar en producción
5. **Duplicación de datos** es intencional (dos tablas)
6. **No hay JOINs** - cada tabla optimizada para su query

---

## 📊 CASSANDRA NO TIENE VISTAS (COMO SQL)

**Diferencia con SQL:**
- SQL: Vistas (views) que son queries guardadas
- Cassandra: **Materialized Views** (tablas físicas, no queries)

### **Materialized View en Cassandra:**

```cql
-- Crear una vista materializada (NO RECOMENDADO en producción)
CREATE MATERIALIZED VIEW transacciones_por_ciudad AS
    SELECT * FROM transacciones_por_usuario
    WHERE ciudad IS NOT NULL
    PRIMARY KEY (ciudad, id_usuario, timestamp, id_transaccion);
```

**⚠️ Problema:** Las Materialized Views tienen bugs y bajo rendimiento.

**✅ Solución:** Crear tablas separadas y mantenerlas sincronizadas en la aplicación (lo que hacemos).

---

¡Guarda este documento para referencia durante tu presentación! 📚
