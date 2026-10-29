# Casos de prueba rápidos

Hoja corta para tener a la mano en la demo. El detalle de cada prueba está en `PLAN_DE_PRUEBAS.md`.

**Antes:** generar los datos al menos una hora antes de la demo. Si no, la regla de frecuencia le suma 20 puntos a todo y hasta una compra normal puede salir rechazada.

## Secuencia en el panel

Mismo usuario (uno con base en CDMX), en este orden y sin dejar pasar mucho tiempo entre una y otra. País siempre México y moneda MXN.

| # | Comercio | Ciudad | Monto | MCC | Sale | Puntos | Qué se activa |
|---|---|---|---|---|---|---|---|
| 1 | Walmart | CDMX | 150.50 | 5411 | `APROBADO` | 0 | Nada |
| 2 | Walmart | Guadalajara | 15000 | 5411 | `RECHAZADO` | 70 | Monto y ubicación |
| 3 | Walmart | CDMX | 15000 | 5411 | `REVISION_MANUAL` | 40 | Monto |
| 4 | Oxxo | Guadalajara | 100 | 5411 | `REVISION_MANUAL` | 30 | Ubicación |
| 5 | Apuestas | Guadalajara | 300 | 7995 | `APROBADO` | 0 o 10 | Categoría, si nunca había usado el 7995 |

Cómo explicarlo:

- **1.** Compra normal en su ciudad.
- **2.** Monto fuera de lo normal y en otra ciudad a segundos de la anterior. Con dos señales se rechaza, y como se rechazó no se guarda.
- **3.** Solo el monto. Una señal fuerte sola no rechaza, la manda a revisión. Esta sí se guarda.
- **4.** Monto normal, pero la compra anterior fue en CDMX hace segundos. Es el viaje imposible.
- **5.** Apuestas es categoría de riesgo, pero por sí sola suma poco. Sirve para mostrar que el sistema no castiga una sola señal débil.

En algunos usuarios el 15000 no alcanza a marcarse como monto raro porque el generador ya les había metido compras muy altas. Si pasa, se nota porque en la 2 sale `REVISION_MANUAL` con 30. Lo más fácil es cambiar de usuario.

## Por API (con el MCC que el panel no tiene)

```bash
curl -X POST http://localhost:8000/analizar-transaccion -H "Content-Type: application/json" -d "{\"id_usuario\": \"<uuid>\", \"monto\": 15000, \"moneda\": \"MXN\", \"comercio\": \"Casa de empeño\", \"ciudad\": \"CDMX\", \"pais\": \"Mexico\", \"mcc\": 5933}"
```

Si se corre justo después de la secuencia de arriba, sale `RECHAZADO` con 80: ubicación, monto y categoría.

Otras rápidas:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/usuarios
curl "http://localhost:8000/historial/<uuid>?limite=5"
curl http://localhost:8000/estadisticas/<uuid>
```

## En cqlsh

```sql
USE finanzas;
DESCRIBE TABLE transacciones_por_usuario;
SELECT DISTINCT id_usuario FROM transacciones_por_usuario;
SELECT timestamp, monto, comercio, ciudad FROM transacciones_por_usuario WHERE id_usuario = <uuid> LIMIT 5;
SELECT * FROM transacciones_por_id WHERE id_transaccion = <timeuuid>;
SELECT * FROM transacciones_por_usuario WHERE ciudad = 'CDMX';   -- falla: pide ALLOW FILTERING
```

## Referencia

| MCC | Qué es | ¿En la lista de riesgo? |
|---|---|---|
| 5411 | Supermercados | No |
| 5812 | Restaurantes | No |
| 5814 | Cafeterías | No |
| 5541 | Gasolineras | No |
| 5999 | Comercio en línea | No |
| 7995 | Apuestas | Sí |
| 5933 | Casas de empeño | Sí (solo por API) |

Montos del generador: las compras normales van de 20 a 500 pesos. Las fraudulentas de monto alto van de 5,000 a 15,000, y las que mezclan varias señales llegan a 20,000.

## Si algo falla

- **No aparecen usuarios:** falta correr `python src/data_generator.py`.
- **La API no responde:** revisar que `python src/api.py` siga corriendo y que el contenedor esté arriba (`docker ps`).
- **Cassandra no conecta:** `docker start cassandra-fraud` y esperar un minuto.
- **Todo sale rechazado:** los datos se generaron hace menos de una hora.
