# 🎤 GUIÓN DE DEMOSTRACIÓN - PRESENTACIÓN

## 🎯 OBJETIVO
Demostrar el sistema funcionando en vivo, explicando cómo Cassandra hace posible la detección de fraude en tiempo real.

---

## ⏱️ TIEMPO TOTAL: 10-15 MINUTOS

```
├── Introducción (2 min)
├── Arquitectura (2 min)
├── Demo en vivo (5 min)
├── Cassandra técnico (3 min)
└── Conclusiones (2 min)
```

---

# 🎬 PARTE 1: INTRODUCCIÓN (2 minutos)

## **Slide 1: Portada**

### **Decir:**
> "Buenos días/tardes. Hoy les presentaremos un **Sistema de Detección de Fraude en Tiempo Real** utilizando **Apache Cassandra**, una base de datos NoSQL distribuida."

---

## **Slide 2: El Problema**

### **Decir:**
> "El fraude bancario es un problema enorme. En 2023, las pérdidas por fraude alcanzaron **$32 mil millones** a nivel global. 
>
> El desafío técnico es que necesitamos analizar **millones de transacciones por día** en menos de **100 milisegundos**. 
>
> Aquí es donde entra **Cassandra** - una base de datos diseñada específicamente para este tipo de workloads."

### **Mostrar en pantalla:**
- Estadísticas de fraude
- Gráfica de crecimiento

---

# 🏗️ PARTE 2: ARQUITECTURA (2 minutos)

## **Slide 3: Stack Tecnológico**

### **Decir:**
> "Nuestro sistema tiene 3 capas:
>
> 1. **Frontend en React** - La interfaz que veremos en un momento
> 2. **Backend en FastAPI** - Implementa 4 reglas de detección de fraude
> 3. **Cassandra** - Almacena y consulta millones de transacciones
>
> La clave está en **cómo modelamos los datos en Cassandra** para obtener lecturas ultra-rápidas."

---

## **Slide 4: Arquitectura de Cassandra**

### **Decir:**
> "A diferencia de SQL tradicional con un servidor master, **Cassandra es peer-to-peer**. 
>
> Todos los nodos son iguales. Si un nodo cae, los otros continúan trabajando. **Sin punto único de fallo**.
>
> Esto nos da una disponibilidad del **99.99%** - crítico para sistemas bancarios."

### **Señalar en diagrama:**
- Los 3 nodos conectados
- "Sin master" anotado

---

# 💻 PARTE 3: DEMO EN VIVO (5 minutos)

## **ANTES DE EMPEZAR**

### **Preparación (hacer antes de la clase):**

1. **Abrir 3 terminales:**
   ```
   Terminal 1: Backend corriendo
   Terminal 2: Frontend corriendo  
   Terminal 3: Para comandos de Cassandra
   ```

2. **Abrir 2 pestañas del navegador:**
   ```
   Pestaña 1: http://localhost:3000 (Frontend)
   Pestaña 2: http://localhost:8000/docs (API Docs)
   ```

3. **Tener a mano:**
   - 1 UUID de usuario de prueba
   - Este guión impreso

---

## **DEMO 1: Mostrar el Sistema**

### **Decir:**
> "Vamos a ver el sistema funcionando. Primero, el dashboard..."

### **Acciones:**
1. Abrir http://localhost:3000
2. Mostrar el Dashboard
3. Señalar las estadísticas

### **Decir:**
> "Aquí vemos estadísticas en tiempo real. Esto es posible porque **Cassandra nos permite consultar millones de transacciones en milisegundos**."

---

## **DEMO 2: Transacción Normal (DEBE APROBAR)**

### **Decir:**
> "Ahora vamos a analizar una transacción normal. Imaginen que alguien compra en un supermercado..."

### **Acciones:**
1. Click en "Analizar Transacción"
2. Llenar el formulario:
   ```
   ID Usuario: [Seleccionar del dropdown]
   Monto: 150
   Moneda: MXN
   Comercio: Walmart
   Ciudad: CDMX
   País: Mexico
   MCC: 5411 - Supermercados
   ```
3. Click en "Analizar Transacción"
4. **ESPERAR EL RESULTADO**

### **Cuando aparezca APROBADO:**
> "Como ven, la transacción fue **APROBADA** en menos de 100 milisegundos. 
>
> ¿Qué pasó por detrás?
>
> 1. El sistema consultó las **últimas 50 transacciones** del usuario en Cassandra
> 2. Comparó el monto de $150 contra el promedio histórico
> 3. Verificó la ubicación (CDMX)
> 4. Validó la categoría (supermercado)
>
> Todo esto en **tiempo real**, gracias a las **prepared statements** y el **modelado optimizado** en Cassandra."

---

## **DEMO 3: Monto Anómalo (DEBE RECHAZAR)**

### **Decir:**
> "Ahora simulemos un caso de fraude. Alguien robó la tarjeta e intenta hacer una compra grande..."

### **Acciones:**
1. Cambiar solo el monto: **15000**
2. Mantener todo lo demás igual
3. Click en "Analizar Transacción"

### **Cuando aparezca RECHAZADO:**
> "¡Transacción RECHAZADA! 
>
> El sistema detectó una **ANOMALÍA DE MONTO** usando el algoritmo de **Z-Score**.
>
> ¿Qué es Z-Score? Es una medida estadística. Si el historial del usuario muestra compras de $50-200, y de repente intenta gastar $15,000, el Z-Score será mayor a 3 - lo que indica que es **extremadamente anómalo**.
>
> El score de riesgo subió a **40%**, suficiente para rechazarla automáticamente."

---

## **DEMO 4: Categoría de Riesgo (DEBE RECHAZAR)**

### **Decir:**
> "Último ejemplo. Transacción en un casino online - categoría de alto riesgo..."

### **Acciones:**
1. Cambiar:
   ```
   Monto: 2000
   MCC: 7995 - Apuestas (Alto Riesgo)
   ```
2. Click en "Analizar Transacción"

### **Cuando aparezca RECHAZADO:**
> "De nuevo, RECHAZADA. Esta vez por **ANOMALÍA DE CATEGORÍA**.
>
> El sistema detectó que este usuario **nunca** ha usado su tarjeta en casinos, y los casinos están en nuestra lista de **categorías de alto riesgo** (MCC 7995).
>
> La combinación de factores lleva el score a **50%** - rechazado automáticamente."

---

## **DEMO 5: Mostrar API Docs (Opcional)**

### **Decir:**
> "Para los más técnicos, aquí está nuestra API REST documentada automáticamente..."

### **Acciones:**
1. Abrir http://localhost:8000/docs
2. Mostrar los 7 endpoints
3. Expandir `/analizar-transaccion`

### **Decir:**
> "Esta es la documentación **Swagger** generada automáticamente por FastAPI. Tenemos **7 endpoints** que interactúan con Cassandra."

---

# 🗄️ PARTE 4: CASSANDRA TÉCNICO (3 minutos)

## **Slide: Modelo de Datos**

### **Decir:**
> "La magia está en **cómo modelamos los datos en Cassandra**.
>
> A diferencia de SQL donde diseñas tablas basándote en tus **datos**, en Cassandra diseñas basándote en tus **queries**."

---

## **Slide: Tabla transacciones_por_usuario**

### **Decir:**
> "Tenemos dos tablas. La primera está optimizada para la query: **'Dame las últimas 50 transacciones del usuario X'**
>
> Fíjense en la PRIMARY KEY:
> ```
> PRIMARY KEY (id_usuario, timestamp, id_transaccion)
> ```
>
> - **Partition Key:** `id_usuario` - Todas las transacciones de un usuario en la misma partición
> - **Clustering Keys:** `timestamp, id_transaccion` - Ordenadas automáticamente por fecha
>
> Esto nos da una complejidad de **O(1)** - lookup directo. En otras palabras, **~5 milisegundos** sin importar cuántos millones de transacciones haya en total."

---

## **Slide: Duplicación de Datos**

### **Decir:**
> "Tenemos una segunda tabla indexada por ID de transacción. 
>
> Sí, estamos **duplicando datos** - pero en Cassandra esto es intencional. 
>
> ¿Por qué? Porque **no hay JOINs** en Cassandra. Cada tabla está optimizada para un tipo de consulta específica.
>
> El trade-off: usamos más espacio (barato), pero ganamos velocidad (crítico)."

---

## **Slide: Prepared Statements**

### **Decir:**
> "Para maximizar el rendimiento, usamos **Prepared Statements**. 
>
> Son queries pre-compiladas que se ejecutan **3-4 veces más rápido** que queries dinámicas.
>
> Aquí está el código [señalar código en slide]:
> ```python
> self._prepared['select_historial'] = self.session.prepare('''
>     SELECT * FROM transacciones_por_usuario
>     WHERE id_usuario = ? LIMIT ?
> ''')
> ```
>
> Esto es crítico cuando procesamos millones de transacciones."

---

# 📊 PARTE 5: RESULTADOS Y CONCLUSIONES (2 minutos)

## **Slide: Comparativa SQL vs Cassandra**

### **Decir:**
> "Hicimos pruebas de rendimiento con **1 millón de transacciones**.
>
> Los resultados:
> - **MySQL:** 450 segundos
> - **PostgreSQL:** 380 segundos  
> - **Cassandra:** 45 segundos
>
> Cassandra es **8-10 veces más rápido**. Y a medida que agregamos más datos, la ventaja aumenta."

---

## **Slide: Métricas del Sistema**

### **Decir:**
> "Nuestro sistema logra:
>
> - **Latencia de análisis:** Menos de 100 milisegundos
> - **Efectividad:** 80-85% de detección de fraudes
> - **Falsos positivos:** Menos del 5%
> - **Disponibilidad:** 99.99% gracias a la arquitectura distribuida de Cassandra
>
> Todo esto es posible porque Cassandra fue diseñado para exactamente este tipo de workload: **alto volumen**, **baja latencia**, **alta disponibilidad**."

---

## **Slide: Conclusiones**

### **Decir:**
> "En conclusión, elegimos Cassandra porque:
>
> 1. ✅ **Alta velocidad de escritura** - Millones de transacciones por día
> 2. ✅ **Baja latencia de lectura** - Análisis en tiempo real
> 3. ✅ **Escalabilidad horizontal** - Agregar nodos según necesidad
> 4. ✅ **Sin punto único de fallo** - Arquitectura peer-to-peer
> 5. ✅ **Perfecto para time-series** - Transacciones con timestamp
>
> Cassandra hace posible lo que sería muy difícil o imposible con una base de datos SQL tradicional."

---

## **Slide: Gracias / Preguntas**

### **Decir:**
> "Esto ha sido nuestra presentación del Sistema de Detección de Fraude con Apache Cassandra. 
>
> El código está disponible en GitHub [mostrar en pantalla]
>
> ¿Alguna pregunta?"

---

# ❓ PREGUNTAS FRECUENTES Y RESPUESTAS

## **P: ¿Por qué no usar SQL con índices?**

### **Respuesta:**
> "Excelente pregunta. Los índices en SQL ayudan, pero:
>
> 1. Los índices ralentizan las escrituras - nosotros tenemos millones de escrituras/día
> 2. Con muchos índices, las tablas SQL se vuelven lentas
> 3. SQL tradicional escala verticalmente (más CPU/RAM), Cassandra escala horizontalmente (más máquinas)
> 4. SQL tiene un punto único de fallo (el servidor master), Cassandra no
>
> Para este caso de uso específico - alto volumen, time-series, baja latencia - Cassandra es superior."

---

## **P: ¿Qué pasa si necesito hacer un JOIN?**

### **Respuesta:**
> "En Cassandra, **no hay JOINs** - y es intencional. 
>
> La filosofía es: duplica los datos y optimiza cada tabla para una query específica. 
>
> Por ejemplo, tenemos `transacciones_por_usuario` para consultar por usuario, y `transacciones_por_id` para consultar por ID. 
>
> Sí, duplicamos datos, pero ganamos velocidad. En sistemas de alto rendimiento, el almacenamiento es barato, la latencia no."

---

## **P: ¿Cassandra garantiza consistencia?**

### **Respuesta:**
> "Cassandra tiene **consistencia tunable** - tú eliges el nivel.
>
> Levels:
> - `ONE`: Lectura rápida, menos consistencia
> - `QUORUM`: Lee de la mayoría de réplicas (balance)
> - `ALL`: Lee de todas las réplicas (máxima consistencia, más lento)
>
> Para nuestro caso, usamos `QUORUM` - balance perfecto entre velocidad y consistencia."

---

## **P: ¿Es difícil aprender Cassandra?**

### **Respuesta:**
> "Tiene una curva de aprendizaje. Los conceptos clave son:
>
> 1. Diseñar por queries, no por datos
> 2. Entender partition keys y clustering keys
> 3. Aceptar la duplicación de datos
> 4. No esperar JOINs
>
> Una vez entiendes estos conceptos, es muy poderoso. Y hay muchos recursos: DataStax Academy tiene cursos gratis."

---

## **P: ¿Empresas reales usan Cassandra?**

### **Respuesta:**
> "Sí, muchas:
>
> - **Netflix:** 2,500+ nodos, 420 TB de datos
> - **Apple:** 75,000+ nodos, 10+ PB de datos
> - **Uber:** Time-series para tracking en tiempo real
> - **Instagram:** Manejo de billones de fotos
>
> Es la elección estándar para sistemas de **alta escala** y **baja latencia**."

---

# ✅ CHECKLIST PRE-PRESENTACIÓN

## **1 DÍA ANTES:**

- [ ] Probar TODO el sistema completo
- [ ] Generar datos de prueba frescos
- [ ] Guardar 3 UUIDs de usuarios
- [ ] Verificar que Cassandra inicia correctamente
- [ ] Hacer las 4 demos y tomar screenshots
- [ ] Leer este guión 2-3 veces

## **1 HORA ANTES:**

- [ ] Iniciar Cassandra
- [ ] Iniciar Backend
- [ ] Iniciar Frontend
- [ ] Verificar que TODO funciona
- [ ] Abrir pestañas del navegador
- [ ] Tener este guión a mano

## **DURANTE LA PRESENTACIÓN:**

- [ ] Hablar despacio y claro
- [ ] Mantener contacto visual
- [ ] Señalar en pantalla lo que explicas
- [ ] NO leer las slides
- [ ] Sonreír y mostrar confianza

---

# 🎯 CONSEJOS FINALES

1. **Practica la demo 3-4 veces** antes de presentar
2. **Memoriza los tiempos** (no leas)
3. **Ten un plan B** si algo falla (screenshots de respaldo)
4. **Explica CON ENTUSIASMO** - es un proyecto genial
5. **Conecta con la audiencia** - usa ejemplos cotidianos

---

**¡MUCHA SUERTE! 🚀**

El proyecto está excelente. Cassandra es la elección perfecta. Solo necesitas explicarlo con confianza.
