# Sistema de detección de fraude: documentación

Este documento junta en un solo lugar cómo está armado el proyecto, cómo se instala y qué hace cada parte. Para lo específico de Cassandra está `DOCUMENTO_TECNICO_CASSANDRA.md`, y para probarlo, `PLAN_DE_PRUEBAS.md`.

## 1. Qué hace

Cuando llega una transacción con tarjeta, el sistema la compara con el historial reciente del usuario y responde en el momento una de tres cosas: `APROBADO`, `REVISION_MANUAL` o `RECHAZADO`. La respuesta trae el puntaje de riesgo, las reglas que se activaron y un mensaje que explica la decisión.

Partes:

- **Cassandra** guarda las transacciones. Corre en Docker con un solo nodo.
- **FastAPI** (Python) expone la API y contiene el motor de reglas.
- **React** con Tailwind es el panel para capturar transacciones y ver el resultado.

## 2. Recorrido de una transacción

1. El panel (o cualquier cliente) manda un `POST /analizar-transaccion` con usuario, monto, moneda, comercio, ciudad, país y MCC.
2. La API valida el cuerpo con Pydantic. Si falta un campo o el monto no es mayor a cero, responde 422.
3. `FraudDetector` pide a Cassandra las últimas 50 transacciones del usuario. Es una sola lectura a una partición, ya ordenada de la más reciente a la más vieja.
4. Se aplican las cuatro reglas y se suman los puntos.
5. Con el puntaje se decide el estado.
6. Si quedó aprobada o en revisión, se guarda en las dos tablas. Las rechazadas no se guardan para que no ensucien el historial con el que se evalúan las siguientes.
7. La API regresa el resultado y si la transacción se guardó.

## 3. Motor de reglas

Está en `src/fraud_detector.py` y todos los números salen de `config/config.py`.

**Ubicación (30 puntos).** Si la ciudad es distinta a la de la última transacción guardada y entre las dos pasaron menos de 30 minutos, se marca `ANOMALIA_GEOGRAFICA`. Solo compara contra la última, no contra todo el historial.

**Monto (40 puntos).** Calcula el promedio y la desviación estándar de los montos del historial y saca el z-score del monto nuevo. Si pasa de 3 se marca `ANOMALIA_MONTO`. Necesita al menos 3 transacciones previas. Si la desviación es cero, usa 1 para no dividir entre cero.

**Frecuencia (20 puntos).** Cuenta cuántas transacciones del historial caen en la última hora y las compara contra un promedio por hora, que sale de dividir el historial entre 24. Si hay más de 5 veces ese promedio, se marca `ANOMALIA_FRECUENCIA`. Solo aplica con 10 o más transacciones previas.

**Categoría (10 puntos).** Si el MCC está en la lista de alto riesgo y el usuario nunca lo había usado, se marca `ANOMALIA_CATEGORIA`. La lista es 7995 (apuestas), 5993 (tabaco), 7273 (citas), 5122 (medicamentos sin receta) y 5933 (casas de empeño).

**Decisión.**

| Puntos | Estado |
|---|---|
| 50 o más | `RECHAZADO` |
| 30 a 49 | `REVISION_MANUAL` |
| menos de 30 | `APROBADO` |

Un usuario sin historial siempre sale aprobado porque no hay contra qué comparar.

Los pesos están puestos para que ninguna regla rechace sola. El monto, que es la más fuerte, deja la transacción en revisión. Para rechazar se necesitan al menos dos señales, por ejemplo monto y ubicación, o monto y categoría.

## 4. Modelo de datos

Keyspace `finanzas` con `SimpleStrategy` y factor de replicación 1, que es lo que tiene sentido con un solo nodo.

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

La primera sirve para el historial y la segunda para buscar una transacción suelta. El porqué de este diseño está en el documento técnico.

## 5. API

Corre en el puerto 8000. Swagger queda en `/docs`.

| Método | Ruta | Qué regresa |
|---|---|---|
| GET | `/` | Nombre del servicio, versión y lista de rutas |
| GET | `/health` | `healthy` si la API tiene sesión abierta con Cassandra |
| POST | `/analizar-transaccion` | Resultado del análisis |
| GET | `/historial/{id_usuario}?limite=50` | Transacciones del usuario (límite entre 1 y 1000) |
| GET | `/transaccion/{id_transaccion}` | Una transacción |
| GET | `/usuarios?limite=100` | IDs de usuarios con transacciones |
| GET | `/estadisticas/{id_usuario}` | Total, monto total y promedio, ciudades y comercios más frecuentes |

Respuesta de `/analizar-transaccion` cuando hay algo raro:

```json
{
  "status": "REVISION_MANUAL",
  "score_riesgo": 40.0,
  "banderas_rojas": ["ANOMALIA_MONTO (Z-Score: 5.12)"],
  "motivo": "Requiere revisión manual - Score: 40.0% - Anomalías: ANOMALIA_MONTO (Z-Score: 5.12)",
  "transaccion_guardada": true
}
```

Las estadísticas por usuario se calculan en Python con `Counter` sobre el historial, porque Cassandra no agrupa por columnas que no son parte de la llave.

CORS permite `localhost:3000` y `localhost:8000`. Para servir el panel desde otro origen hay que agregarlo en `CORS_ORIGINS`.

## 6. Panel

Tiene dos pestañas:

- **Dashboard**: cuatro tarjetas con totales de transacciones, aprobadas, rechazadas y en revisión. Por ahora los números están fijos en el componente y no vienen de la API.
- **Analizar transacción**: un formulario con el usuario (lista que se llena con `/usuarios`), monto, moneda (MXN, USD o EUR), comercio, ciudad, país y MCC. El MCC se escoge de una lista: 5411, 5812, 5814, 5541, 5999 y 7995. Al enviar muestra el estado en verde, amarillo o rojo, el puntaje y las banderas.

Si la API no responde al cargar, la lista de usuarios usa un ID de ejemplo para que el formulario no quede vacío.

## 7. Instalación

Requisitos: Python 3, Node.js y Docker.

```bash
docker run --name cassandra-fraud -p 9042:9042 -d cassandra:latest
python -m venv venv
venv\Scripts\activate          # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
python scripts/init_database.py
python src/data_generator.py
python src/api.py
```

Y en otra terminal:

```bash
cd frontend
npm install
npm start
```

Después de la primera vez, `start.bat` (Windows) o `start.sh` (Linux/Mac) arrancan el contenedor, la API y el panel.

`scripts/validate_project.py` revisa la versión de Python, que estén los archivos y que las dependencias se puedan importar. Sirve cuando algo no arranca y no queda claro por qué.

## 8. Datos de prueba

`src/data_generator.py` crea tres usuarios con ciudad base en CDMX, Guadalajara y Monterrey, con 40, 35 y 30 transacciones. Alrededor del 10 % son fraudulentas: montos de 5,000 a 15,000, compras en el extranjero, comercios de apuestas o tabaco, o una mezcla de todo.

Hay que tener en cuenta que el generador guarda todas las transacciones con la hora del momento en que corre. Durante la primera hora, todas cuentan como recientes para la regla de frecuencia y cualquier análisis suma 20 puntos de más. Si la ciudad de la última transacción generada es distinta, también se activa la de ubicación. Para probar con resultados normales hay que generar los datos al menos una hora antes.

## 9. Configuración

Todo está en `config/config.py`:

| Variable | Valor | Para qué |
|---|---|---|
| `HISTORIAL_LIMITE` | 50 | Transacciones que se leen para comparar |
| `Z_SCORE_UMBRAL` | 3.0 | Desde dónde un monto es anómalo |
| `TIEMPO_MINIMO_VIAJE` | 30 | Minutos mínimos entre dos ciudades |
| `UMBRAL_RECHAZO` | 50 | Puntos para rechazar |
| `UMBRAL_REVISION` | 30 | Puntos para revisión manual |
| `PESO_ANOMALIA_*` | 30 / 40 / 20 / 10 | Puntos de cada regla |
| `MCC_ALTO_RIESGO` | 5 códigos | Categorías vigiladas |

Para hacerlo más estricto se bajan los umbrales o el z-score; para que moleste menos, al revés.

## 10. Problemas comunes

- **La API no conecta a Cassandra.** El contenedor tarda cerca de un minuto en aceptar conexiones. Con `docker logs cassandra-fraud` se ve cuándo dice que ya escucha clientes CQL. Si el contenedor está detenido: `docker start cassandra-fraud`.
- **`ModuleNotFoundError: config`.** Los scripts se corren desde la raíz del proyecto (`python src/api.py`), no desde dentro de `src/`.
- **El puerto 8000 está ocupado.** Se cambia `API_PORT` en la configuración. El panel tiene la URL fija, así que hay que cambiarla también en `App.js` y en `TransactionAnalyzer.jsx`.
- **El panel dice "Network Error".** La API no está corriendo o el origen no está en `CORS_ORIGINS`.
- **Todo sale rechazado justo después de generar datos.** Es lo que se explica en la sección 8.

## 11. Limitaciones conocidas

- La regla de frecuencia supone que el historial cubre 24 horas. Con usuarios que compran poco, el promedio por hora sale muy bajo y la regla se dispara con pocas compras.
- La de ubicación solo ve la ciudad. No sabe que CDMX y Toluca están a una hora, ni que Tijuana y San Diego están pegadas.
- Las transacciones rechazadas no quedan registradas en ningún lado, así que no hay forma de auditarlas después.
- `/health` solo revisa que exista la sesión. Si Cassandra se cae después de arrancar la API, sigue respondiendo `healthy`.
- Las tarjetas del dashboard tienen números fijos.
- Algunos textos del panel tienen los acentos mal codificados (por ejemplo "TransacciÃ³n").
