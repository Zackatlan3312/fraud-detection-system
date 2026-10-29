# Detección de fraude en transacciones

Proyecto de la materia Bases de Datos NoSQL, hecho con Diego Herminio Ortíz Villalba en diciembre de 2025. Una API recibe cada transacción nueva, la compara con el historial del usuario y decide si se aprueba, se rechaza o se manda a revisión manual. Los datos están en Apache Cassandra, el backend es FastAPI y el panel está hecho en React con Tailwind.

## Cómo decide

Cada transacción suma puntos de riesgo según cuatro reglas. El historial que se usa son las últimas 50 transacciones del usuario.

| Regla | Qué revisa | Puntos |
|---|---|---|
| Ubicación | La ciudad es distinta a la de la compra anterior y pasaron menos de 30 minutos | 30 |
| Monto | El z-score del monto contra el historial es mayor a 3 | 40 |
| Frecuencia | En la última hora hubo más de 5 veces el promedio de transacciones por hora (solo si hay al menos 10 en el historial) | 20 |
| Categoría | El MCC es de alto riesgo (apuestas, tabaco, citas, medicamentos sin receta, casas de empeño) y el usuario nunca lo había usado | 10 |

Con 50 puntos o más se rechaza, de 30 a 49 va a revisión manual y con menos de 30 se aprueba. Las aprobadas y las de revisión se guardan en el historial; las rechazadas no. Un usuario sin historial se aprueba directo porque no hay con qué comparar.

Los pesos, umbrales y la lista de MCC están en `config/config.py`.

## Modelo en Cassandra

Keyspace `finanzas` con dos tablas que guardan lo mismo, cada una pensada para una consulta, porque Cassandra no hace joins:

- `transacciones_por_usuario`: partición por `id_usuario` y orden por `timestamp` descendente. De aquí lee el detector el historial reciente.
- `transacciones_por_id`: para traer una transacción por su `timeuuid`.

Al guardar una transacción se escribe en las dos.

## Cómo correrlo

Necesitas Python 3, Node.js y Docker.

```bash
docker run --name cassandra-fraud -p 9042:9042 -d cassandra:latest
python -m venv venv
venv\Scripts\activate          # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
python scripts/init_database.py
python src/data_generator.py     # opcional, crea 3 usuarios con unas 100 transacciones
python src/api.py
```

Cassandra tarda cerca de un minuto en aceptar conexiones después del `docker run`. `init_database.py` espera a que esté lista antes de crear el keyspace.

El panel va en otra terminal:

```bash
cd frontend
npm install
npm start
```

La API queda en http://localhost:8000 (con Swagger en `/docs`) y el panel en http://localhost:3000. Ya instalado todo, `start.bat` o `start.sh` levantan Cassandra, la API y el panel de una vez.

## Endpoints

| Método | Ruta | Para qué |
|---|---|---|
| POST | `/analizar-transaccion` | Analiza una transacción y la guarda si no se rechaza |
| GET | `/historial/{id_usuario}` | Historial del usuario (`?limite=50`) |
| GET | `/transaccion/{id_transaccion}` | Una transacción por ID |
| GET | `/usuarios` | Usuarios que tienen transacciones |
| GET | `/estadisticas/{id_usuario}` | Totales, promedio, ciudades y comercios frecuentes |
| GET | `/resumen` | Transacciones guardadas y decisiones tomadas desde que arrancó la API |
| GET | `/health` | Estado de la API y de la conexión |

Ejemplo de cuerpo para `/analizar-transaccion`:

```json
{
  "id_usuario": "550e8400-e29b-41d4-a716-446655440000",
  "monto": 1500.00,
  "moneda": "MXN",
  "comercio": "Walmart",
  "ciudad": "CDMX",
  "pais": "Mexico",
  "mcc": 5411
}
```

## Dónde está cada cosa

- `src/fraud_detector.py`: las cuatro reglas y la decisión final
- `src/database.py`: conexión y consultas a Cassandra
- `src/api.py`: endpoints
- `src/data_generator.py`: datos de prueba con transacciones normales y fraudulentas
- `scripts/init_database.py`: crea el keyspace y las tablas
- `frontend/`: panel en React

Los `.md` de la raíz son el material de la entrega: la documentación completa, el documento técnico de Cassandra, las consultas CQL, el plan y los casos de prueba, y la presentación con su guion.

## Pendientes

- La regla de frecuencia supone que el historial cubre unas 24 horas para sacar el promedio por hora. Con usuarios que compran poco, ese promedio sale bajo.
- El frontend tiene la URL de la API fija en `localhost:8000`.
