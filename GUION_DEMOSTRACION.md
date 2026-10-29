# Guion de la presentación

Unos 12 minutos en total. Las diapositivas están en `PRESENTACION_CASSANDRA.md` y los datos de la demo en `CASOS_PRUEBA_RAPIDOS.md`.

| Parte | Diapositivas | Tiempo |
|---|---|---|
| Problema y por qué Cassandra | 1 a 3 | 2 min |
| Arquitectura y modelo de datos | 4 a 10 | 4 min |
| Reglas y demo | 11 a 13 | 5 min |
| Mejoras y preguntas | 14 y 15 | 1 min más preguntas |

## Preparación

**El día anterior**

- Correr todo de principio a fin una vez.
- Tomar capturas de cada paso de la demo, por si algo falla en vivo.

**Al menos una hora antes**

- Arrancar Cassandra y correr `python src/data_generator.py`. Tiene que ser con una hora de anticipación como mínimo: el generador guarda todo con la hora del momento, y durante la primera hora la regla de frecuencia le suma puntos a cualquier compra.
- Anotar un UUID de un usuario con base en CDMX.

**Diez minutos antes**

- Levantar la API y el panel.
- Dejar abiertas tres pestañas: el panel en la de análisis, `localhost:8000/docs` y una terminal con `cqlsh` ya dentro de `finanzas`.

## 1. Problema (diapositivas 1 y 2)

> Cada vez que alguien paga con tarjeta, el banco tiene que decidir en ese momento si la compra es de esa persona o no. Para decidir necesita compararla con lo que esa persona hace normalmente: en qué ciudad compra, cuánto gasta, cada cuánto. O sea que en cada compra hay que leer su historial y casi siempre escribir una fila nueva.

## 2. Por qué Cassandra (diapositiva 3)

> Ese patrón, de escribir mucho y leer siempre igual, por usuario y por fecha, es justo para lo que está hecha Cassandra. Las escrituras no leen nada antes, y si diseñamos bien la tabla, el historial de un usuario queda guardado junto y ya ordenado.
>
> Lo que perdemos son los joins y poder consultar por cualquier columna. Para este sistema no importa, porque desde el principio sabemos qué consultas vamos a hacer.

## 3. Arquitectura y modelo (diapositivas 4 a 10)

**Diapositiva 4.** Señalar las tres capas de arriba hacia abajo.

> El panel en React manda la transacción a la API en FastAPI. Ahí está el detector, que pide el historial a Cassandra, aplica las reglas y regresa la decisión.

**Diapositiva 5.**

> Usamos un solo nodo, así que el factor de replicación es 1. En un banco real serían tres réplicas por centro de datos.

**Diapositiva 6.** Esta es la más importante. Ir parte por parte de la llave.

> La llave de partición es el usuario, así que todo su historial vive en el mismo nodo. Dentro de la partición, las filas están ordenadas por fecha de la más nueva a la más vieja, y por eso traer las últimas 50 es leer las primeras 50, sin ordenar nada. El ID de la transacción va al final para que dos compras en el mismo milisegundo no se pisen, porque en Cassandra un insert con la misma llave sobrescribe.

**Diapositivas 7 y 8.**

> Para buscar una transacción por su ID tenemos otra tabla con los mismos datos. En SQL sería un índice; en Cassandra se hace una tabla por consulta y se escribe en las dos. Gastamos más espacio, pero cada lectura va directa.

**Diapositiva 9.** Si da tiempo, cambiar a `cqlsh` y correr:

```sql
SELECT timestamp, monto, ciudad FROM transacciones_por_usuario WHERE id_usuario = <uuid> LIMIT 5;
SELECT * FROM transacciones_por_usuario WHERE ciudad = 'CDMX';
```

> La primera responde de inmediato. La segunda Cassandra ni siquiera la ejecuta: pide `ALLOW FILTERING` porque tendría que recorrer toda la tabla.

**Diapositiva 10.**

> Todas las consultas de la aplicación son prepared statements. Cassandra las analiza una vez y después solo recibe los valores, lo que además evita la inyección.

## 4. Reglas y demo (diapositivas 11 a 13)

**Diapositivas 11 y 12.**

> Son cuatro reglas y cada una suma puntos. Las pensamos para que ninguna rechace sola: la más fuerte, la del monto, da 40, y se rechaza desde 50. Para rechazar hacen falta dos señales.

**Demo.** Cambiar al panel y usar siempre el mismo usuario.

1. Walmart, CDMX, 150.50, MCC 5411. Sale **aprobada con 0**.
   > Compra normal, en su ciudad, por lo que suele gastar.
2. Walmart, Guadalajara, 15000. Sale **rechazada con 70**.
   > El monto está muy por encima de lo normal y además está en Guadalajara, segundos después de comprar en CDMX. Dos señales, se rechaza. Y como se rechazó, no se guarda.
3. Walmart, CDMX, 15000. Sale **revisión manual con 40**.
   > El mismo monto, pero ahora en su ciudad. Una sola señal, aunque sea fuerte, no rechaza. La manda a que la revise una persona.
4. Oxxo, Guadalajara, 100. Sale **revisión manual con 30**.
   > El monto es normal, pero hace unos segundos compró en CDMX. No se puede estar en las dos ciudades. Es el viaje imposible.

Para cerrar, abrir la pestaña Dashboard. Debe marcar 1 aprobada, 1 rechazada y 2 en revisión, que son las cuatro compras de la demo. Por eso conviene que la API se haya iniciado justo antes de presentar.

Si sobra tiempo, abrir `/docs` y enseñar que la misma prueba se puede hacer desde Swagger.

Si en el paso 2 sale revisión con 30 en lugar de rechazo, ese usuario tiene montos altos en su historial y el 15000 no se ve raro. Cambiar a otro usuario y repetir desde el paso 1.

## 5. Mejoras (diapositiva 14)

> Si esto fuera a producción cambiaríamos varias cosas. Partiríamos el historial por mes para que la partición no crezca para siempre. Meteríamos las dos inserciones en un batch para que no quede una sin la otra. Guardaríamos las rechazadas en otra tabla para poder auditarlas. Y usaríamos tres réplicas con quorum.

## Preguntas que pueden salir

**¿Por qué no SQL con índices?**

> A este tamaño, un PostgreSQL con un índice en usuario y fecha funcionaría igual. La diferencia aparece con volumen: cuando las escrituras ya no caben en un servidor, Cassandra crece agregando nodos y no tiene un servidor principal que se pueda caer.

**¿Y si necesitan un join?**

> No hay. Se duplican los datos en una tabla pensada para esa consulta, como hicimos con la tabla por ID.

**¿Qué consistencia usan?**

> La que trae el driver por defecto, que es que responda un nodo. Con un solo nodo da igual. Con tres réplicas usaríamos quorum para leer y escribir, y así cada lectura ve la última escritura. En este sistema importa: si no vemos la compra de hace un minuto, no detectamos el viaje imposible.

**¿Por qué no usaron machine learning?**

> Con reglas cada decisión se puede explicar: la respuesta dice exactamente qué se activó. Para entrenar un modelo necesitaríamos transacciones reales etiquetadas como fraude o no, y no las tenemos.

**¿Las estadísticas por ciudad se sacan con CQL?**

> No. Cassandra solo agrupa por columnas de la llave. Esas cuentas las hace la API en Python sobre el historial del usuario.
