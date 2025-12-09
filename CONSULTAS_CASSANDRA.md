# 📊 CONSULTAS CASSANDRA - SISTEMA DE DETECCIÓN DE FRAUDE

## 🔌 CONECTAR A CASSANDRA

```bash
docker exec -it cassandra-fraud cqlsh
```

```cql
USE finanzas;
```

---

## 📋 CONSULTAS BÁSICAS

### **1. Ver estructura de tablas**

```cql
DESCRIBE TABLES;
```

```cql
DESCRIBE TABLE transacciones_por_usuario;
```

```cql
DESCRIBE TABLE transacciones_por_id;
```

---

### **2. Contar transacciones totales**

```cql
SELECT COUNT(*) FROM transacciones_por_usuario;
```

---

### **3. Listar usuarios con transacciones**

```cql
SELECT DISTINCT id_usuario FROM transacciones_por_usuario LIMIT 10;
```

---

## 👤 CONSULTAS POR USUARIO

### **4. Ver transacciones de un usuario (RÁPIDA - Partition Key)**

```cql
SELECT timestamp, monto, moneda, comercio, ciudad, pais
FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
LIMIT 10;
```

**⚡ Tiempo:** ~5ms (gracias a partition key)

---

### **5. Ver todas las transacciones de un usuario**

```cql
SELECT *
FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46;
```

---

### **6. Contar transacciones de un usuario**

```cql
SELECT COUNT(*)
FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46;
```

---

### **7. Ver transacciones por rango de fechas**

```cql
SELECT timestamp, monto, comercio, ciudad
FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
  AND timestamp >= '2025-12-01 00:00:00'
  AND timestamp <= '2025-12-08 23:59:59';
```

---

### **8. Ver transacciones más recientes (ordenadas automáticamente)**

```cql
SELECT timestamp, monto, comercio
FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
LIMIT 5;
```

**Nota:** Ya están ordenadas por `timestamp DESC` (más reciente primero)

---

## 💳 CONSULTAS POR ID DE TRANSACCIÓN

### **9. Buscar transacción por ID (ULTRA-RÁPIDA)**

```cql
SELECT *
FROM transacciones_por_id
WHERE id_transaccion = 6ba7b810-9dad-11d1-80b4-00c04fd430c8;
```

**⚡ Tiempo:** ~2ms (lookup directo)

---

### **10. Ver detalles completos de una transacción**

```cql
SELECT id_transaccion, id_usuario, timestamp, monto, moneda, comercio, ciudad, pais, mcc
FROM transacciones_por_id
WHERE id_transaccion = 6ba7b810-9dad-11d1-80b4-00c04fd430c8;
```

---

## 📊 ESTADÍSTICAS Y ANÁLISIS

### **11. Ver distribución por país**

```cql
SELECT pais, COUNT(*) as total
FROM transacciones_por_usuario
GROUP BY pais
ALLOW FILTERING;
```

**⚠️ Advertencia:** `ALLOW FILTERING` es ineficiente. Solo para demos.

---

### **12. Ver transacciones por ciudad**

```cql
SELECT id_usuario, timestamp, monto, comercio
FROM transacciones_por_usuario
WHERE ciudad = 'CDMX'
ALLOW FILTERING
LIMIT 20;
```

**⚠️ Ineficiente:** Escanea todas las particiones.

---

### **13. Ver transacciones mayores a un monto**

```cql
SELECT id_usuario, timestamp, monto, comercio, ciudad
FROM transacciones_por_usuario
WHERE monto > 1000
ALLOW FILTERING
LIMIT 10;
```

**⚠️ Ineficiente:** Cassandra no está optimizado para filtros numéricos.

---

### **14. Ver transacciones por categoría (MCC)**

```cql
SELECT id_usuario, timestamp, monto, comercio, mcc
FROM transacciones_por_usuario
WHERE mcc = 5411
ALLOW FILTERING
LIMIT 10;
```

---

## 🔍 CONSULTAS PARA ANÁLISIS DE FRAUDE

### **15. Ver últimas transacciones de un usuario (para detección)**

```cql
SELECT timestamp, monto, moneda, comercio, ciudad, pais, mcc
FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
LIMIT 50;
```

**Uso:** El detector de fraude usa esto para calcular Z-Score y patrones.

---

### **16. Ver transacciones en una ciudad específica de un usuario**

```cql
SELECT timestamp, monto, comercio
FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
  AND ciudad = 'CDMX'
ALLOW FILTERING;
```

---

### **17. Ver transacciones en rango de monto para un usuario**

```cql
SELECT timestamp, monto, comercio, ciudad
FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
  AND monto > 500
  AND monto < 2000
ALLOW FILTERING;
```

---

## 🛠️ CONSULTAS DE ADMINISTRACIÓN

### **18. Ver información del keyspace**

```cql
SELECT * FROM system_schema.keyspaces WHERE keyspace_name = 'finanzas';
```

---

### **19. Ver columnas de una tabla**

```cql
SELECT column_name, type, kind
FROM system_schema.columns
WHERE keyspace_name = 'finanzas'
  AND table_name = 'transacciones_por_usuario';
```

---

### **20. Ver índices de una tabla**

```cql
SELECT * FROM system_schema.indexes WHERE keyspace_name = 'finanzas';
```

---

### **21. Ver información del cluster**

```cql
SELECT cluster_name, partitioner FROM system.local;
```

---

### **22. Ver nodos del cluster**

```cql
SELECT peer, data_center, rack FROM system.peers;
```

---

## ⚡ CONSULTAS OPTIMIZADAS vs INEFICIENTES

### **✅ OPTIMIZADA: Con partition key**

```cql
SELECT * FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
LIMIT 10;
```
**Complejidad:** O(1) - ~5ms

---

### **✅ OPTIMIZADA: Con partition key + clustering key**

```cql
SELECT * FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
  AND timestamp > '2025-12-01'
  AND timestamp < '2025-12-08';
```
**Complejidad:** O(log n) - ~10ms

---

### **❌ INEFICIENTE: Sin partition key**

```cql
SELECT * FROM transacciones_por_usuario
WHERE monto > 1000
ALLOW FILTERING;
```
**Complejidad:** O(n) - puede ser MUY lento

---

### **❌ INEFICIENTE: Filtro por columna no indexada**

```cql
SELECT * FROM transacciones_por_usuario
WHERE ciudad = 'CDMX'
ALLOW FILTERING;
```
**Problema:** Escanea TODAS las particiones.

---

## 📝 CONSULTAS DE INSERCIÓN

### **23. Insertar transacción en tabla por usuario**

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
    3c25fe57-8e1e-4a2b-9030-de0a5ee28d46,
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

### **24. Insertar transacción en tabla por ID**

```cql
INSERT INTO transacciones_por_id (
    id_transaccion,
    id_usuario,
    timestamp,
    monto,
    moneda,
    comercio,
    ciudad,
    pais,
    mcc
) VALUES (
    6ba7b810-9dad-11d1-80b4-00c04fd430c8,
    3c25fe57-8e1e-4a2b-9030-de0a5ee28d46,
    '2025-12-08 10:30:00',
    250.50,
    'MXN',
    'Oxxo',
    'CDMX',
    'Mexico',
    5411
);
```

---

## 🗑️ CONSULTAS DE ELIMINACIÓN

### **25. Eliminar una transacción específica**

```cql
DELETE FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
  AND timestamp = '2025-12-08 10:30:00'
  AND id_transaccion = 6ba7b810-9dad-11d1-80b4-00c04fd430c8;
```

**⚠️ Importante:** Necesitas TODA la PRIMARY KEY.

---

### **26. Eliminar todas las transacciones de un usuario**

```cql
DELETE FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46;
```

---

### **27. Truncar tabla (eliminar TODO)**

```cql
TRUNCATE transacciones_por_usuario;
```

**⚠️ CUIDADO:** Esto elimina TODOS los datos.

---

## 🔄 CONSULTAS DE ACTUALIZACIÓN

### **28. Actualizar una transacción**

```cql
UPDATE transacciones_por_usuario
SET monto = 300.00
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
  AND timestamp = '2025-12-08 10:30:00'
  AND id_transaccion = 6ba7b810-9dad-11d1-80b4-00c04fd430c8;
```

**⚠️ Importante:** En Cassandra, UPDATE es como INSERT (upsert).

---

## 🎯 CONSULTAS PARA LA DEMO

### **Demo 1: Mostrar estructura**

```cql
USE finanzas;
DESCRIBE TABLES;
DESCRIBE TABLE transacciones_por_usuario;
```

**Explicar:** Partition key, clustering keys, orden DESC.

---

### **Demo 2: Contar transacciones**

```cql
SELECT COUNT(*) FROM transacciones_por_usuario;
```

**Decir:** "Tenemos X transacciones en el sistema"

---

### **Demo 3: Listar usuarios**

```cql
SELECT DISTINCT id_usuario FROM transacciones_por_usuario LIMIT 5;
```

**Copiar un UUID para siguiente demo.**

---

### **Demo 4: Ver transacciones (RÁPIDA)**

```cql
SELECT timestamp, monto, moneda, comercio, ciudad, pais
FROM transacciones_por_usuario
WHERE id_usuario = [PEGAR UUID]
LIMIT 10;
```

**Explicar:** "Esta query tarda ~5ms gracias a la partition key."

---

### **Demo 5: Buscar por ID**

```cql
-- Copiar un id_transaccion de la demo anterior
SELECT * FROM transacciones_por_id
WHERE id_transaccion = [PEGAR TIMEUUID];
```

**Explicar:** "Por eso tenemos dos tablas - cada una optimizada para su query."

---

### **Demo 6: Query ineficiente (OPCIONAL)**

```cql
SELECT id_usuario, monto, comercio
FROM transacciones_por_usuario
WHERE monto > 1000
ALLOW FILTERING
LIMIT 10;
```

**Explicar:** "ALLOW FILTERING significa query ineficiente. Evitar en producción."

---

## 📊 CONSULTAS ÚTILES PARA ANÁLISIS

### **29. Ver promedio de monto por usuario**

```cql
-- Nota: Cassandra no soporta AVG directamente
-- Hacer en la aplicación:
SELECT monto FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46;

-- Calcular promedio en Python/JavaScript
```

---

### **30. Ver ciudades más frecuentes de un usuario**

```cql
SELECT ciudad, COUNT(*) as total
FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
GROUP BY ciudad
ALLOW FILTERING;
```

---

### **31. Ver comercios más frecuentes**

```cql
SELECT comercio, COUNT(*) as total
FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
GROUP BY comercio
ALLOW FILTERING;
```

---

### **32. Ver transacciones por moneda**

```cql
SELECT moneda, COUNT(*) as total
FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
GROUP BY moneda
ALLOW FILTERING;
```

---

## 🔑 CONCEPTOS CLAVE

### **Partition Key (id_usuario)**
- Determina en qué nodo físico se almacenan los datos
- Queries con partition key son ultra-rápidas (O(1))
- Ejemplo: `WHERE id_usuario = ...`

---

### **Clustering Keys (timestamp, id_transaccion)**
- Definen el orden DENTRO de la partición
- Ordenados automáticamente
- Ejemplo: `timestamp DESC` = más reciente primero

---

### **PRIMARY KEY**
```
PRIMARY KEY (id_usuario, timestamp, id_transaccion)
        ↑              ↑                  ↑
  Partition Key  Clustering Key   Clustering Key
```

---

### **ALLOW FILTERING**
- ⚠️ Significa "query ineficiente"
- Escanea TODAS las particiones
- Solo usar para demos/desarrollo
- En producción: crear tabla específica para esa query

---

### **Duplicación de Datos**
- Cassandra NO tiene JOINs
- Creamos dos tablas:
  - `transacciones_por_usuario` → Query por usuario
  - `transacciones_por_id` → Query por ID
- Duplicación es INTENCIONAL (optimización)

---

## 📱 CHEAT SHEET PARA IMPRIMIR

```
===============================================
CONSULTAS RÁPIDAS - CASSANDRA
===============================================

CONECTAR:
docker exec -it cassandra-fraud cqlsh
USE finanzas;

VER ESTRUCTURA:
DESCRIBE TABLES;
DESCRIBE TABLE transacciones_por_usuario;

LISTAR USUARIOS:
SELECT DISTINCT id_usuario 
FROM transacciones_por_usuario LIMIT 5;

VER TRANSACCIONES (RÁPIDA):
SELECT timestamp, monto, comercio, ciudad
FROM transacciones_por_usuario
WHERE id_usuario = [UUID]
LIMIT 10;

CONTAR TOTAL:
SELECT COUNT(*) FROM transacciones_por_usuario;

BUSCAR POR ID:
SELECT * FROM transacciones_por_id
WHERE id_transaccion = [TIMEUUID];

SALIR:
EXIT;

===============================================
CONCEPTOS CLAVE:
- Partition Key = id_usuario (nodo físico)
- Clustering Keys = timestamp, id_transaccion (orden)
- ALLOW FILTERING = ineficiente (evitar)
- Duplicación = intencional (optimización)
===============================================
```

---

**Creado:** Diciembre 2025  
**Versión:** 1.0  
**Para:** Sistema de Detección de Fraude con Cassandra
