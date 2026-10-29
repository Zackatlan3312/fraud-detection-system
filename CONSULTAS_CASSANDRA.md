# Consultas CQL

Consultas para revisar los datos directamente en Cassandra. En los ejemplos hay que cambiar los UUID por los que aparezcan en tu base; el generador de datos los imprime al correr y también salen con la consulta 3.

## Conectarse

```bash
docker exec -it cassandra-fraud cqlsh
```

```sql
USE finanzas;
```

Si se prefiere un menú en lugar de escribir CQL, `python explorar_cassandra.py` hace casi todo lo de abajo.

## Estructura

```sql
DESCRIBE TABLES;
DESCRIBE TABLE transacciones_por_usuario;
DESCRIBE TABLE transacciones_por_id;

-- columnas y qué papel tienen en la llave
SELECT column_name, type, kind
FROM system_schema.columns
WHERE keyspace_name = 'finanzas' AND table_name = 'transacciones_por_usuario';

-- configuración de replicación
SELECT * FROM system_schema.keyspaces WHERE keyspace_name = 'finanzas';
```

## Por usuario

Todas estas usan la llave de partición, así que van directo a un solo lugar.

```sql
-- 1. últimas 10 transacciones (ya salen ordenadas de la más nueva a la más vieja)
SELECT timestamp, monto, moneda, comercio, ciudad, mcc
FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
LIMIT 10;

-- 2. cuántas tiene, cuánto suman y el promedio
SELECT COUNT(*), SUM(monto), AVG(monto), MAX(monto)
FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46;

-- rango de fechas: funciona porque timestamp es columna de agrupamiento
SELECT timestamp, monto, comercio, ciudad
FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
  AND timestamp >= '2025-11-01' AND timestamp < '2025-12-01';

-- filtrar por ciudad dentro de un solo usuario: lleva ALLOW FILTERING,
-- pero como está acotado a una partición el costo es pequeño
SELECT timestamp, monto, comercio
FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46 AND ciudad = 'CDMX'
ALLOW FILTERING;
```

## Usuarios

```sql
-- 3. qué usuarios hay
SELECT DISTINCT id_usuario FROM transacciones_por_usuario LIMIT 10;
```

`DISTINCT` está permitido porque `id_usuario` es la llave de partición, aunque recorre todas las particiones para armar la lista.

## Por ID de transacción

```sql
SELECT * FROM transacciones_por_id
WHERE id_transaccion = 6ba7b810-9dad-11d1-80b4-00c04fd430c8;

-- la fecha va dentro del timeuuid
SELECT id_transaccion, toTimestamp(id_transaccion), monto
FROM transacciones_por_id
WHERE id_transaccion = 6ba7b810-9dad-11d1-80b4-00c04fd430c8;
```

## Consultas que recorren toda la tabla

Funcionan con los datos de prueba, pero son las que no se deben hacer en producción. Sirven para mostrar la diferencia.

```sql
-- total de filas: no usa llave, lee todo
SELECT COUNT(*) FROM transacciones_por_usuario;

-- sin ALLOW FILTERING, Cassandra rechaza estas tres
SELECT id_usuario, timestamp, monto, comercio FROM transacciones_por_usuario
WHERE ciudad = 'CDMX' ALLOW FILTERING;

SELECT id_usuario, timestamp, monto, comercio FROM transacciones_por_usuario
WHERE monto > 5000 ALLOW FILTERING;

SELECT id_usuario, timestamp, monto, comercio FROM transacciones_por_usuario
WHERE mcc = 7995 ALLOW FILTERING;
```

Lo que no se puede hacer es agrupar por columnas que no son de la llave, como `GROUP BY ciudad` o `GROUP BY pais`. Cassandra solo agrupa por columnas de la llave primaria. Esas cuentas se hacen en la aplicación: `/estadisticas/{id_usuario}` las calcula en Python.

## Insertar a mano

Hay que escribir en las dos tablas con los mismos valores, que es lo que hace `database.py`.

```sql
INSERT INTO transacciones_por_usuario
  (id_usuario, timestamp, id_transaccion, monto, moneda, comercio, ciudad, pais, mcc)
VALUES
  (3c25fe57-8e1e-4a2b-9030-de0a5ee28d46, toTimestamp(now()), now(), 250.00, 'MXN', 'Oxxo', 'CDMX', 'Mexico', 5411);
```

`now()` genera un `timeuuid` nuevo. Para la segunda tabla hay que usar el mismo ID, así que conviene copiarlo de la primera:

```sql
SELECT id_transaccion, timestamp FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46 LIMIT 1;

INSERT INTO transacciones_por_id
  (id_transaccion, id_usuario, timestamp, monto, moneda, comercio, ciudad, pais, mcc)
VALUES
  (<id copiado>, 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46, '<timestamp copiado>', 250.00, 'MXN', 'Oxxo', 'CDMX', 'Mexico', 5411);
```

## Modificar y borrar

`UPDATE` y `DELETE` de una fila necesitan la llave primaria completa.

```sql
UPDATE transacciones_por_usuario SET comercio = 'Oxxo Centro'
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
  AND timestamp = '2025-11-20 18:32:10.123+0000'
  AND id_transaccion = 6ba7b810-9dad-11d1-80b4-00c04fd430c8;

DELETE FROM transacciones_por_usuario
WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
  AND timestamp = '2025-11-20 18:32:10.123+0000'
  AND id_transaccion = 6ba7b810-9dad-11d1-80b4-00c04fd430c8;

-- todo el historial de un usuario (la partición completa)
DELETE FROM transacciones_por_usuario WHERE id_usuario = 3c25fe57-8e1e-4a2b-9030-de0a5ee28d46;

-- vaciar las tablas para empezar de cero
TRUNCATE transacciones_por_usuario;
TRUNCATE transacciones_por_id;
```

En Cassandra un `UPDATE` sobre una llave que no existe crea la fila, y un `INSERT` sobre una que existe la sobrescribe. No hay error en ninguno de los dos casos.

## Clúster

```sql
SELECT cluster_name, release_version FROM system.local;
SELECT peer, data_center, rack FROM system.peers;   -- vacío con un solo nodo
```
