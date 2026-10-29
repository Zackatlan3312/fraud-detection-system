# Detección de fraude con Apache Cassandra

Contenido de las diapositivas. Lo que se dice en cada una está en `GUION_DEMOSTRACION.md`.

---

## 1. Portada

**Detección de fraude en transacciones con Apache Cassandra**

Diego Herminio Ortíz Villalba y Jorge Marcos Sánchez Sánchez

Bases de Datos NoSQL · 8 de diciembre de 2025

---

## 2. El problema

- Cada compra con tarjeta hay que aprobarla o rechazarla en el momento.
- Para decidir hay que comparar contra lo que esa persona hace normalmente: dónde compra, cuánto gasta, cada cuánto.
- Eso significa leer su historial en cada compra y escribir una fila nueva casi siempre.
- Muchas escrituras y una sola forma de leer: por usuario y por fecha.

---

## 3. Por qué Cassandra

| Lo que necesita el sistema | Lo que da Cassandra |
|---|---|
| Escribir muchas transacciones | Escrituras sin lectura previa: commit log y memoria |
| Leer el historial reciente de un usuario | Todo el usuario en una partición, ya ordenado por fecha |
| No caerse | Sin servidor principal; cualquier nodo atiende |
| Crecer | Se agregan nodos |

Lo que se pierde: joins, consultas libres por cualquier columna y transacciones entre tablas.

---

## 4. Arquitectura

```
React (puerto 3000)
      |  HTTP / JSON
FastAPI (puerto 8000)
  api.py -> fraud_detector.py -> database.py
      |  CQL, prepared statements
Cassandra (Docker, puerto 9042)
  keyspace finanzas
    transacciones_por_usuario
    transacciones_por_id
```

---

## 5. Keyspace

```sql
CREATE KEYSPACE finanzas
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
```

- Un solo nodo, una réplica.
- En producción: `NetworkTopologyStrategy` con tres réplicas por centro de datos.

---

## 6. Tabla por usuario

```sql
PRIMARY KEY (id_usuario, timestamp, id_transaccion)
WITH CLUSTERING ORDER BY (timestamp DESC)
```

- `id_usuario`: llave de partición. Todo el historial vive en un solo lugar.
- `timestamp DESC`: guardado de lo más nuevo a lo más viejo.
- `id_transaccion`: evita que dos compras en el mismo milisegundo se pisen.

Consulta del detector: `WHERE id_usuario = ? LIMIT 50`.

---

## 7. Tabla por ID

```sql
id_transaccion timeuuid PRIMARY KEY
```

- Para traer una transacción suelta.
- El `timeuuid` trae la fecha adentro: `toTimestamp(id_transaccion)`.

---

## 8. ¿Por qué dos tablas con lo mismo?

- Cassandra no hace joins ni filtra bien por columnas que no son llave.
- Se diseña una tabla por consulta y se escribe en las dos.
- Se paga con espacio. Se gana que cada lectura vaya directo.

---

## 9. Consultas

| Consulta | ¿Usa la llave? | Costo |
|---|---|---|
| Historial de un usuario | Sí | Una partición |
| Rango de fechas de un usuario | Sí (partición + agrupamiento) | Una partición |
| Transacción por ID | Sí | Una partición |
| Todas las compras en CDMX | No, pide `ALLOW FILTERING` | Toda la tabla |
| Compras por ciudad (`GROUP BY`) | No se puede | Se hace en Python |

---

## 10. Prepared statements

```python
stmt = session.prepare(
    "SELECT ... FROM transacciones_por_usuario WHERE id_usuario = ? LIMIT ?"
)
session.execute(stmt, (id_usuario, 50))
```

- Cassandra analiza la consulta una sola vez.
- Los valores viajan aparte: no hay inyección de CQL.

---

## 11. Las reglas

| Regla | Se activa cuando | Puntos |
|---|---|---|
| Ubicación | Otra ciudad a menos de 30 min de la compra anterior | 30 |
| Monto | z-score mayor a 3 contra las últimas 50 | 40 |
| Frecuencia | Más de 5 veces el promedio por hora | 20 |
| Categoría | MCC de riesgo que nunca había usado | 10 |

---

## 12. La decisión

| Puntos | Resultado |
|---|---|
| 50 o más | Rechazada (no se guarda) |
| 30 a 49 | Revisión manual (se guarda) |
| Menos de 30 | Aprobada (se guarda) |

Ninguna regla rechaza sola. Hacen falta al menos dos señales.

---

## 13. Demo

- Panel: http://localhost:3000
- API: http://localhost:8000/docs

| Compra | Resultado |
|---|---|
| Walmart CDMX, $150 | Aprobada, 0 |
| Walmart Guadalajara, $15,000 | Rechazada, 70 |
| Walmart CDMX, $15,000 | Revisión, 40 |
| Oxxo Guadalajara, $100 | Revisión, 30 |

---

## 14. Lo que mejoraríamos

- Partición por usuario y mes, para que no crezca sin límite.
- Las dos inserciones en un `BATCH` para que no queden a medias.
- Guardar también las rechazadas, en otra tabla, para poder auditarlas.
- Tres réplicas y lecturas y escrituras con `QUORUM`.
- Una regla de ubicación que use distancia real y no solo el nombre de la ciudad.

---

## 15. Preguntas
