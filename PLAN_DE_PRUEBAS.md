# Plan de pruebas

Pruebas para revisar que la base, la API y el panel hacen lo que deben. Están en el orden en que conviene correrlas: si falla algo de Cassandra, lo demás va a fallar también.

## Antes de empezar

1. Levantar Cassandra (`docker start cassandra-fraud`) y esperar a que acepte conexiones.
2. Correr `python scripts/init_database.py`.
3. Correr `python src/data_generator.py` y anotar los tres UUID que imprime.
4. **Esperar al menos una hora** antes de las pruebas de análisis (partes 2.3 y 3.3).

El último punto importa. El generador guarda todas las transacciones con la hora en que corre. Durante esa primera hora, la regla de frecuencia ve decenas de compras "recientes" y le suma 20 puntos a cualquier análisis. Si además la ciudad de la última transacción generada no coincide con la de la prueba, se activa también la de ubicación. Los resultados esperados de abajo suponen datos con más de una hora.

Los resultados de las secuencias de análisis se comprobaron corriendo el detector contra 300 historiales generados al azar. En más del 90 % de los casos salió lo indicado. Las excepciones son usuarios a los que el generador les metió muchos montos altos, lo que sube tanto la desviación estándar que 15,000 ya no pasa de un z-score de 3. En esos casos la bandera de monto no aparece y el puntaje baja 40.

## Parte 1: Cassandra

Se corren en `cqlsh` (`docker exec -it cassandra-fraud cqlsh`, luego `USE finanzas;`).

| # | Prueba | Cómo | Resultado esperado |
|---|---|---|---|
| 1 | Existe el keyspace | `SELECT * FROM system_schema.keyspaces WHERE keyspace_name = 'finanzas';` | Una fila con `SimpleStrategy` y `replication_factor: 1` |
| 2 | Existen las tablas | `DESCRIBE TABLES;` | `transacciones_por_id` y `transacciones_por_usuario` |
| 3 | Llave de la tabla por usuario | `DESCRIBE TABLE transacciones_por_usuario;` | `PRIMARY KEY (id_usuario, timestamp, id_transaccion)` y `CLUSTERING ORDER BY (timestamp DESC, ...)` |
| 4 | Llave de la tabla por ID | `DESCRIBE TABLE transacciones_por_id;` | `id_transaccion timeuuid PRIMARY KEY` |
| 5 | Se generaron los datos | `SELECT COUNT(*)` en las dos tablas | 105 en cada una (40 + 35 + 30). Si los números no coinciden entre tablas, falló alguna inserción |
| 6 | Hay tres usuarios | `SELECT DISTINCT id_usuario FROM transacciones_por_usuario;` | Los tres UUID que imprimió el generador |
| 7 | El historial sale ordenado | `SELECT timestamp, monto FROM transacciones_por_usuario WHERE id_usuario = <uuid> LIMIT 5;` | Cinco filas de la más nueva a la más vieja, sin `ORDER BY` |
| 8 | La tabla por ID tiene lo mismo | Copiar un `id_transaccion` de la prueba 7 y buscarlo en `transacciones_por_id` | La misma transacción con los mismos datos |
| 9 | Cassandra bloquea consultas sin llave | `SELECT * FROM transacciones_por_usuario WHERE ciudad = 'CDMX';` | Error que pide `ALLOW FILTERING`. Con `ALLOW FILTERING` al final sí responde |
| 10 | No se puede agrupar por ciudad | `SELECT ciudad, COUNT(*) FROM transacciones_por_usuario GROUP BY ciudad;` | Error: `GROUP BY` solo acepta columnas de la llave primaria |

## Parte 2: API

Con la API corriendo (`python src/api.py`). Se pueden hacer con `curl` o desde Swagger en http://localhost:8000/docs.

### 2.1 Generales

| # | Prueba | Petición | Resultado esperado |
|---|---|---|---|
| 11 | Raíz | `GET /` | JSON con `servicio`, `version: 2.0.0` y la lista de rutas |
| 12 | Salud | `GET /health` | `status: healthy`, `database: connected`, `keyspace: finanzas` |
| 13 | Salud sin base | Detener el contenedor y repetir | Debería responder `unhealthy`, pero hoy sigue diciendo `healthy`: el endpoint solo revisa que exista la sesión, no hace ninguna consulta. Después volver a arrancar el contenedor |
| 14 | Documentación | Abrir `/docs` | Swagger con las siete rutas agrupadas en General, Análisis y Consultas |

### 2.2 Consultas

| # | Prueba | Petición | Resultado esperado |
|---|---|---|---|
| 15 | Usuarios | `GET /usuarios` | `total_usuarios: 3` y la lista de UUID |
| 16 | Historial | `GET /historial/<uuid>?limite=5` | `total_transacciones: 5`, de la más nueva a la más vieja |
| 17 | Límite fuera de rango | `GET /historial/<uuid>?limite=0` | 400, "Límite debe estar entre 1 y 1000" |
| 18 | Estadísticas | `GET /estadisticas/<uuid>` | Total, monto total, promedio, y ciudades y comercios más frecuentes. La ciudad base del usuario debe salir primero |
| 19 | Transacción por ID | `GET /transaccion/<id de la prueba 8>` | Los datos de esa transacción |
| 20 | Transacción que no existe | `GET /transaccion/<timeuuid válido inventado>` | 404, "Transacción no encontrada" |

### 2.3 Análisis

Todas con `POST /analizar-transaccion` y el mismo usuario (uno con CDMX como ciudad base). **Van en este orden y seguidas**, porque cada transacción aprobada o en revisión se guarda y cambia el historial de la siguiente.

| # | Transacción | Resultado esperado | Por qué |
|---|---|---|---|
| 21 | Monto `0` | 422 | Pydantic exige monto mayor a cero |
| 22 | Walmart, CDMX, 150.50 MXN, MCC 5411 | `APROBADO`, 0 puntos, `transaccion_guardada: true` | Monto normal, ciudad de siempre |
| 23 | Walmart, Guadalajara, 15000 MXN, MCC 5411 | `RECHAZADO`, 70 puntos, `transaccion_guardada: false` | Monto fuera de rango (40) y otra ciudad a segundos de la anterior (30) |
| 24 | Walmart, CDMX, 15000 MXN, MCC 5411 | `REVISION_MANUAL`, 40 puntos | Solo el monto. La 23 no se guardó, así que la última sigue siendo CDMX |
| 25 | Oxxo, Guadalajara, 100 MXN, MCC 5411 | `REVISION_MANUAL`, 30 puntos | Viaje imposible: la anterior fue en CDMX hace segundos |
| 26 | Casa de empeño, CDMX, 15000 MXN, MCC 5933 | `RECHAZADO`, 80 puntos | Ubicación (la anterior fue Guadalajara), monto y una categoría que el usuario nunca usó. El generador no produce el 5933, así que esa bandera siempre aparece. En algunos usuarios el 15000 de la prueba 24 ya subió la desviación, el monto no se marca y queda en `REVISION_MANUAL` con 40 |
| 27 | Usuario nuevo (un UUID que no esté en la base), cualquier compra | `APROBADO`, "Usuario nuevo - sin historial para comparar" | No hay contra qué comparar |

Después de la secuencia, `GET /historial/<uuid>?limite=5` debe mostrar arriba las transacciones 25, 24 y 22, y no la 23 ni la 26, porque las rechazadas no se guardan.

## Parte 3: Panel

Con el panel corriendo (`npm start` en `frontend/`), en http://localhost:3000.

### 3.1 Carga

| # | Prueba | Resultado esperado |
|---|---|---|
| 28 | Abrir la página | Barra superior, pestañas "Dashboard" y "Analizar Transacción", y el pie de página |
| 29 | Dashboard | Cuatro tarjetas: Total, Aprobadas, Rechazadas y En revisión. **Los números son fijos (90, 65, 20 y 5)**, el componente todavía no los pide a la API |
| 30 | Ancho de celular | Con la ventana angosta, las tarjetas se apilan en una columna |

### 3.2 Formulario

| # | Prueba | Resultado esperado |
|---|---|---|
| 31 | Lista de usuarios | Los tres usuarios, mostrados con los primeros 8 caracteres del UUID |
| 32 | Enviar vacío | El navegador no deja enviar y marca el primer campo obligatorio |
| 33 | Lista de MCC | 5411, 5812, 5814, 5541, 5999 y 7995. El 5933 no está, así que la prueba 26 solo se puede hacer por API |

### 3.3 Análisis desde el panel

Con un usuario distinto al de la parte 2.3, o con datos recién regenerados y una hora de espera.

| # | Transacción | Resultado esperado |
|---|---|---|
| 34 | Walmart, CDMX, 150.50, MXN, México, 5411 | Tarjeta verde, `APROBADO`, 0 % |
| 35 | Walmart, Guadalajara, 15000, MXN, México, 5411 | Tarjeta roja, `RECHAZADO`, 70 %, banderas de ubicación y monto |
| 36 | Walmart, CDMX, 15000, MXN, México, 5411 | Tarjeta naranja, `REVISION_MANUAL`, 40 % |
| 37 | Oxxo, Guadalajara, 100, MXN, México, 5411 | Tarjeta naranja, `REVISION_MANUAL`, 30 %, bandera de ubicación |
| 38 | Apuestas, Guadalajara, 300, MXN, México, 7995 | Tarjeta verde, `APROBADO`. Si el usuario nunca había usado el 7995 sale con 10 % y una bandera de categoría; si ya lo había usado, 0 % |

La prueba 38 sirve para mostrar que la categoría por sí sola no cambia la decisión.

### 3.4 Errores

| # | Prueba | Resultado esperado |
|---|---|---|
| 39 | Detener la API y analizar | Tarjeta gris con `ERROR` y "Error al conectar con el servidor" |
| 40 | Recargar con la API detenida | La lista de usuarios muestra un ID de ejemplo (`550e8400...`) en lugar de quedar vacía |

## Pendientes que se ven al probar

- `/health` no detecta que Cassandra se cayó (prueba 13).
- Las tarjetas del dashboard no están conectadas a la API (prueba 29).
- Algunos textos del panel tienen los acentos mal codificados, por ejemplo el botón dice "Analizar TransacciÃ³n".
