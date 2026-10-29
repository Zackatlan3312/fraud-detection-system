# Cassandra en el sistema de detección de fraude

Este documento explica por qué se usó Cassandra, cómo se diseñaron las tablas y qué cambiaría si el sistema tuviera que aguantar tráfico real.

## 1. Por qué Cassandra

El detector hace siempre lo mismo. Por cada compra lee las últimas 50 transacciones de un usuario y, si la aprueba, escribe una más. Son muchas escrituras y una sola forma de leer: por usuario y ordenado por fecha. Cassandra está hecha para ese patrón.

- **Escribir es barato.** Una escritura va al commit log y a una tabla en memoria, sin leer nada antes. No hay bloqueos ni índices que actualizar.
- **La lectura del historial es una sola partición.** Todos los movimientos de un usuario viven juntos y ya están ordenados, así que traer los últimos 50 no requiere ordenar ni buscar.
- **Crece agregando nodos.** No hay un servidor principal. Cualquier nodo recibe lecturas y escrituras, y si uno se cae los demás siguen.

A cambio no hay joins, no se puede consultar por cualquier columna y cada tabla se diseña pensando en una consulta específica. Para este proyecto eso no estorba porque las consultas se conocen desde el principio.

Siendo justos, a la escala de este proyecto un PostgreSQL con un índice en `(id_usuario, timestamp)` resolvería la misma consulta igual de rápido. La diferencia se nota cuando el volumen de escrituras ya no cabe en un solo servidor o cuando el sistema no puede detenerse por mantenimiento.

## 2. Keyspace

```sql
CREATE KEYSPACE IF NOT EXISTS finanzas
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
```

Con un solo nodo en Docker no tiene sentido replicar. En un clúster real se usaría `NetworkTopologyStrategy` con tres réplicas por centro de datos:

```sql
CREATE KEYSPACE finanzas
WITH replication = {'class': 'NetworkTopologyStrategy', 'dc1': 3};
```

## 3. Tabla `transacciones_por_usuario`

```sql
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

La llave primaria tiene tres partes y cada una tiene un motivo:

- **`id_usuario` es la llave de partición.** Decide en qué nodo vive el dato. Todas las transacciones de un usuario quedan en la misma partición, así que leer su historial toca un solo nodo.
- **`timestamp` es la primera columna de agrupamiento**, en orden descendente. Dentro de la partición, las filas se guardan en disco de la más reciente a la más vieja. Por eso `LIMIT 50` regresa justo las últimas 50 sin ordenar nada.
- **`id_transaccion` es la segunda.** Si dos transacciones del mismo usuario cayeran en el mismo milisegundo, sin esta columna tendrían la misma llave y la segunda sobrescribiría a la primera. En Cassandra un `INSERT` con una llave que ya existe actualiza la fila en lugar de fallar.

La consulta que usa el detector:

```sql
SELECT monto, ciudad, pais, timestamp, mcc, comercio, moneda, id_transaccion
FROM transacciones_por_usuario
WHERE id_usuario = ?
LIMIT ?;
```

## 4. Tabla `transacciones_por_id`

```sql
CREATE TABLE finanzas.transacciones_por_id (
    id_transaccion timeuuid PRIMARY KEY,
    id_usuario uuid,
    timestamp timestamp,
    monto decimal,
    moneda text,
    comercio text,
    ciudad text,
    pais text,
    mcc int
);
```

Sirve para una sola cosa: traer una transacción cuando ya se tiene su ID, por ejemplo para revisar un caso marcado. Cada transacción es su propia partición.

El ID es un `timeuuid`, que Python genera con `uuid.uuid1()`. Además de ser único, lleva dentro la fecha en que se creó, y Cassandra puede extraerla con `toTimestamp(id_transaccion)`.

## 5. Por qué los datos están duplicados

En SQL habría una sola tabla con dos índices. En Cassandra no se puede consultar eficientemente por una columna que no sea parte de la llave, así que se hace una tabla por cada forma de leer y se escribe en las dos.

El costo es el doble de espacio y que la aplicación tiene que mantener las dos tablas iguales. En `database.py` las dos inserciones son dos `execute` separados. Si la segunda fallara, la transacción quedaría en una tabla y no en la otra. Lo correcto sería mandarlas en un `BATCH` con log, que garantiza que se apliquen las dos o ninguna:

```sql
BEGIN BATCH
  INSERT INTO transacciones_por_usuario (...) VALUES (...);
  INSERT INTO transacciones_por_id (...) VALUES (...);
APPLY BATCH;
```

## 6. Cómo escribe y lee Cassandra

**Escritura.** El dato se agrega al commit log, que existe para recuperarse si el nodo se cae, y a la memtable en memoria. En ese momento ya se confirma. Cuando la memtable se llena se vacía a disco como un SSTable, un archivo que ya no se modifica. Con el tiempo, la compactación junta varios SSTables en uno.

**Lectura.** Se busca en la memtable y en los SSTables que puedan tener la partición. Para no abrir archivos de más, cada SSTable tiene un filtro de Bloom que dice rápido si la partición seguro no está ahí, y un índice para llegar directo a ella. Por eso las lecturas por llave de partición son rápidas y las que no la usan no.

## 7. Prepared statements

`database.py` prepara cuatro consultas al conectarse: las dos inserciones, la del historial y la búsqueda por ID. Cassandra las analiza una sola vez y después solo recibe los valores. Eso ahorra trabajo en cada llamada y evita armar CQL concatenando texto, que es la puerta a la inyección.

```python
self._prepared_statements['select_historial'] = self.session.prepare("""
    SELECT monto, ciudad, pais, timestamp, mcc, comercio, moneda, id_transaccion
    FROM transacciones_por_usuario
    WHERE id_usuario = ?
    LIMIT ?
""")

rows = self.session.execute(self._prepared_statements['select_historial'], (id_usuario, limite))
```

La consulta de usuarios (`SELECT DISTINCT id_usuario ...`) no está preparada. El límite entra con un f-string, aunque siempre es un entero que viene validado de la API.

## 8. Qué consultas se pueden hacer

Rápidas, porque usan la llave:

```sql
-- historial de un usuario
SELECT * FROM transacciones_por_usuario WHERE id_usuario = ? LIMIT 50;

-- rango de fechas dentro del usuario
SELECT * FROM transacciones_por_usuario
WHERE id_usuario = ? AND timestamp >= '2025-11-01' AND timestamp < '2025-12-01';

-- una transacción por ID
SELECT * FROM transacciones_por_id WHERE id_transaccion = ?;
```

Lentas o prohibidas:

```sql
-- sin llave de partición: Cassandra la rechaza a menos que se agregue ALLOW FILTERING,
-- y con eso recorre todas las particiones de todos los nodos
SELECT * FROM transacciones_por_usuario WHERE ciudad = 'CDMX' ALLOW FILTERING;

-- COUNT(*) sin llave también recorre toda la tabla
SELECT COUNT(*) FROM transacciones_por_usuario;
```

`GROUP BY` solo funciona sobre columnas de la llave primaria, así que algo como "transacciones por ciudad" no se puede pedir en CQL. Por eso `/estadisticas` trae el historial y cuenta en Python.

`SELECT DISTINCT id_usuario` sí es válido porque es la llave de partición, pero también recorre todas las particiones. Con tres usuarios de prueba no importa; con millones habría que tener una tabla aparte de usuarios.

## 9. Consistencia

El código usa el nivel por defecto del driver, `LOCAL_ONE`: basta con que un nodo responda. Con un solo nodo y una réplica da igual el nivel que se elija.

En un clúster con tres réplicas, escribir y leer con `QUORUM` (dos de tres) garantiza que una lectura vea la última escritura, porque los nodos que escriben y los que leen siempre se cruzan en al menos uno. Para un detector de fraude eso importa. Si la lectura no viera la compra de hace un minuto, la regla de ubicación no detectaría el viaje imposible.

## 10. Qué cambiaría para producción

- **Particiones por mes.** Hoy la partición de un usuario crece para siempre. Con la llave `((id_usuario, mes), timestamp, id_transaccion)` cada partición tiene un tamaño acotado. Para el historial bastaría leer el mes actual y, si no alcanza, el anterior.
- **`BATCH` en las dos inserciones**, como se explica en la sección 5.
- **Una tabla de usuarios** en lugar de `SELECT DISTINCT`.
- **Una tabla para las rechazadas.** Hoy no se guardan en ningún lado y no hay forma de auditarlas.
- **Tres réplicas y `QUORUM`**, como en la sección 9.
