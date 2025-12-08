# 📋 PLAN DE PRUEBAS - SISTEMA DE DETECCIÓN DE FRAUDE

## 🎯 OBJETIVO

Este documento contiene todas las pruebas necesarias para validar el correcto funcionamiento del sistema de detección de fraude, incluyendo:
- Pruebas de base de datos (Cassandra)
- Pruebas de API (Backend)
- Pruebas de interfaz gráfica (Frontend)
- Casos de prueba para la demo

---

## 📊 PARTE 1: PRUEBAS DE BASE DE DATOS (CASSANDRA)

### **Pre-requisito:**

```bash
# Verificar que Cassandra esté corriendo
docker ps | grep cassandra-fraud

# Si no está corriendo:
docker start cassandra-fraud
```

---

### **Prueba 1: Verificar Keyspace**

**Objetivo:** Confirmar que el keyspace 'finanzas' existe.

```bash
docker exec -it cassandra-fraud cqlsh
```

```cql
-- Listar todos los keyspaces
SELECT keyspace_name FROM system_schema.keyspaces;
```

**Resultado esperado:**
```
keyspace_name
--------------
system
system_auth
system_distributed
system_schema
finanzas         ← DEBE APARECER
```

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 2: Verificar Tablas**

**Objetivo:** Confirmar que las tablas existen.

```cql
USE finanzas;
DESCRIBE TABLES;
```

**Resultado esperado:**
```
transacciones_por_usuario  transacciones_por_id
```

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 3: Verificar Estructura de Tabla 1**

**Objetivo:** Validar PRIMARY KEY de transacciones_por_usuario.

```cql
DESCRIBE TABLE transacciones_por_usuario;
```

**Resultado esperado:**
```cql
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

**Verificar:**
- ✅ Partition Key: `id_usuario`
- ✅ Clustering Keys: `timestamp, id_transaccion`
- ✅ Orden: `timestamp DESC`

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 4: Verificar Estructura de Tabla 2**

**Objetivo:** Validar PRIMARY KEY de transacciones_por_id.

```cql
DESCRIBE TABLE transacciones_por_id;
```

**Resultado esperado:**
```cql
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

**Verificar:**
- ✅ Primary Key simple: `id_transaccion`

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 5: Insertar Datos de Prueba**

**Objetivo:** Verificar que se pueden insertar transacciones.

```bash
# Salir de cqlsh
EXIT

# Generar datos
cd C:\fraud-detection
python src\data_generator.py
```

**Resultado esperado:**
```
Generando historial para usuario: 3c25fe57...
  ✓ [1/30] NORMAL  | $  150.50 MXN | Oxxo
  ✓ [2/30] NORMAL  | $  250.00 MXN | Walmart
  ...
✓ Historial generado exitosamente
  Transacciones creadas: 30/30
```

**Guardar los 3 UUIDs que aparezcan:**
- Usuario 1: _________________________________
- Usuario 2: _________________________________
- Usuario 3: _________________________________

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 6: Contar Transacciones**

**Objetivo:** Verificar que los datos se insertaron.

```cql
USE finanzas;
SELECT COUNT(*) FROM transacciones_por_usuario;
```

**Resultado esperado:**
```
count
------
90
```

(O el número total de transacciones generadas)

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 7: Listar Usuarios**

**Objetivo:** Obtener UUIDs para pruebas posteriores.

```cql
SELECT DISTINCT id_usuario FROM transacciones_por_usuario LIMIT 10;
```

**Resultado esperado:**
```
id_usuario
---------------------------------------
3c25fe57-8e1e-4a2b-9030-de0a5ee28d46
8385f056-50b2-4c8f-9536-02f838496d69
a1b2c3d4-e5f6-7890-1234-567890abcdef

(3 rows)
```

**Copiar un UUID:** _________________________________

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 8: Query por Partition Key (RÁPIDA)**

**Objetivo:** Validar velocidad de consulta con partition key.

```cql
SELECT timestamp, monto, moneda, comercio, ciudad, pais
FROM transacciones_por_usuario
WHERE id_usuario = [PEGAR UUID DE PRUEBA 7]
LIMIT 10;
```

**Resultado esperado:**
- ✅ Retorna 10 transacciones (o menos si el usuario tiene menos)
- ✅ Ordenadas por timestamp DESC (más reciente primero)
- ✅ Tiempo: < 10ms

**Ejemplo:**
```
timestamp                  | monto  | moneda | comercio  | ciudad | pais
---------------------------+--------+--------+-----------+--------+-------
2025-12-08 15:30:00.000000 | 150.50 | MXN    | Oxxo      | CDMX   | Mexico
2025-12-08 14:20:00.000000 | 250.00 | MXN    | Walmart   | CDMX   | Mexico
...
```

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 9: Query por ID (RÁPIDA)**

**Objetivo:** Validar búsqueda directa por ID.

```cql
-- Primero obtener un id_transaccion de la query anterior
SELECT id_transaccion, timestamp, monto, comercio
FROM transacciones_por_usuario
WHERE id_usuario = [UUID]
LIMIT 1;
```

**Copiar el id_transaccion:** _________________________________

```cql
-- Buscar en la segunda tabla
SELECT *
FROM transacciones_por_id
WHERE id_transaccion = [PEGAR ID_TRANSACCION];
```

**Resultado esperado:**
- ✅ Retorna 1 fila con todos los detalles
- ✅ Tiempo: < 5ms

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 10: Query Ineficiente (ALLOW FILTERING)**

**Objetivo:** Demostrar diferencia de rendimiento.

```cql
SELECT id_usuario, monto, comercio
FROM transacciones_por_usuario
WHERE monto > 1000
ALLOW FILTERING
LIMIT 10;
```

**Resultado esperado:**
- ✅ Retorna transacciones con monto > 1000
- ⚠️  Tiempo: Variable (puede ser lento)
- ⚠️  Advertencia: "ALLOW FILTERING puede ser lento"

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 11: Estadísticas Básicas**

**Objetivo:** Obtener métricas de la base de datos.

```cql
-- Distribución por país
SELECT pais, COUNT(*) 
FROM transacciones_por_usuario 
GROUP BY pais 
ALLOW FILTERING;
```

**Resultado esperado:**
```
pais           | count
---------------+-------
Mexico         | 75
Estados Unidos | 10
Francia        | 5
```

**Estado:** ✅ PASS / ❌ FAIL

---

## 🔌 PARTE 2: PRUEBAS DE API (BACKEND)

### **Pre-requisito:**

```bash
# Terminal separada
cd C:\fraud-detection
venv\Scripts\activate
python src\api.py
```

**Debe mostrar:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✓ Conexión a Cassandra establecida
```

---

### **Prueba 12: Health Check**

**Objetivo:** Verificar que la API está funcionando.

**Método 1: Navegador**
```
http://localhost:8000/health
```

**Método 2: PowerShell**
```powershell
curl http://localhost:8000/health
```

**Resultado esperado:**
```json
{
  "status": "healthy",
  "database": "connected",
  "keyspace": "finanzas"
}
```

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 13: Endpoint Raíz**

**Objetivo:** Verificar información de la API.

```
http://localhost:8000/
```

**Resultado esperado:**
```json
{
  "servicio": "API de Detección de Fraude en Tiempo Real",
  "version": "2.0.0",
  "estado": "activo",
  "endpoints": {
    "documentacion": "/docs",
    "analisis": "/analizar-transaccion",
    ...
  }
}
```

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 14: API Docs (Swagger)**

**Objetivo:** Verificar documentación interactiva.

```
http://localhost:8000/docs
```

**Resultado esperado:**
- ✅ Página de Swagger UI carga correctamente
- ✅ Se muestran todos los endpoints:
  - GET /
  - GET /health
  - POST /analizar-transaccion
  - GET /historial/{id_usuario}
  - GET /transaccion/{id_transaccion}
  - GET /usuarios
  - GET /estadisticas/{id_usuario}

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 15: Obtener Lista de Usuarios**

**Objetivo:** Verificar endpoint de usuarios.

```
http://localhost:8000/usuarios
```

**Resultado esperado:**
```json
{
  "total_usuarios": 3,
  "usuarios": [
    "3c25fe57-8e1e-4a2b-9030-de0a5ee28d46",
    "8385f056-50b2-4c8f-9536-02f838496d69",
    "a1b2c3d4-e5f6-7890-1234-567890abcdef"
  ]
}
```

**Guardar un UUID para pruebas:** _________________________________

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 16: Obtener Historial de Usuario**

**Objetivo:** Verificar endpoint de historial.

```
http://localhost:8000/historial/[PEGAR UUID DE PRUEBA 15]?limite=10
```

**Resultado esperado:**
```json
{
  "id_usuario": "3c25fe57-8e1e-4a2b-9030-de0a5ee28d46",
  "total_transacciones": 10,
  "transacciones": [
    {
      "id_transaccion": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "monto": 150.5,
      "moneda": "MXN",
      "comercio": "Oxxo",
      "ciudad": "CDMX",
      "pais": "Mexico",
      "timestamp": "2025-12-08T15:30:00",
      "mcc": 5411
    },
    ...
  ]
}
```

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 17: Obtener Estadísticas de Usuario**

**Objetivo:** Verificar cálculos de estadísticas.

```
http://localhost:8000/estadisticas/[PEGAR UUID]
```

**Resultado esperado:**
```json
{
  "id_usuario": "3c25fe57-8e1e-4a2b-9030-de0a5ee28d46",
  "total_transacciones": 30,
  "monto_total": 4500.50,
  "monto_promedio": 150.02,
  "ciudades_frecuentes": ["CDMX", "Guadalajara", "Monterrey"],
  "comercios_frecuentes": ["Oxxo", "Walmart", "Soriana"]
}
```

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 18: Analizar Transacción Normal**

**Objetivo:** Validar detección de transacción normal.

**Método: Swagger UI** (http://localhost:8000/docs)

1. Ir a POST /analizar-transaccion
2. Click en "Try it out"
3. Pegar este JSON:

```json
{
  "id_usuario": "3c25fe57-8e1e-4a2b-9030-de0a5ee28d46",
  "monto": 150.50,
  "moneda": "MXN",
  "comercio": "Walmart",
  "ciudad": "CDMX",
  "pais": "Mexico",
  "mcc": 5411
}
```

4. Click "Execute"

**Resultado esperado:**
```json
{
  "status": "APROBADO",
  "score_riesgo": 0.0,
  "banderas_rojas": [],
  "motivo": "Transacción normal según el historial del usuario",
  "transaccion_guardada": true
}
```

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 19: Analizar Transacción con Monto Alto (FRAUDE)**

**Objetivo:** Validar detección de monto anómalo.

**JSON:**
```json
{
  "id_usuario": "3c25fe57-8e1e-4a2b-9030-de0a5ee28d46",
  "monto": 15000.00,
  "moneda": "MXN",
  "comercio": "Walmart",
  "ciudad": "CDMX",
  "pais": "Mexico",
  "mcc": 5411
}
```

**Resultado esperado:**
```json
{
  "status": "RECHAZADO",
  "score_riesgo": 40.0,
  "banderas_rojas": ["ANOMALIA_MONTO (Z-Score: 8.52)"],
  "motivo": "RECHAZADO - Score de riesgo: 40% - Anomalías: ANOMALIA_MONTO",
  "transaccion_guardada": false
}
```

**Verificar:**
- ✅ Status: RECHAZADO
- ✅ Score >= 40
- ✅ Bandera: ANOMALIA_MONTO
- ✅ transaccion_guardada: false

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 20: Analizar Transacción con Categoría de Riesgo (FRAUDE)**

**Objetivo:** Validar detección de MCC de alto riesgo.

**JSON:**
```json
{
  "id_usuario": "3c25fe57-8e1e-4a2b-9030-de0a5ee28d46",
  "monto": 2000.00,
  "moneda": "MXN",
  "comercio": "Casino Online",
  "ciudad": "CDMX",
  "pais": "Mexico",
  "mcc": 7995
}
```

**Resultado esperado:**
```json
{
  "status": "RECHAZADO" o "REVISION_MANUAL",
  "score_riesgo": 30.0 - 50.0,
  "banderas_rojas": ["ANOMALIA_CATEGORIA (MCC: 7995)", "ANOMALIA_MONTO (...)"],
  "motivo": "...",
  "transaccion_guardada": false
}
```

**Verificar:**
- ✅ Detecta ANOMALIA_CATEGORIA
- ✅ MCC 7995 (Casino)

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 21: Analizar Transacción con Ubicación Extraña (FRAUDE)**

**Objetivo:** Validar detección de viaje imposible.

**Paso 1:** Hacer una transacción normal
```json
{
  "id_usuario": "3c25fe57-8e1e-4a2b-9030-de0a5ee28d46",
  "monto": 100.00,
  "moneda": "MXN",
  "comercio": "Oxxo",
  "ciudad": "CDMX",
  "pais": "Mexico",
  "mcc": 5411
}
```

**Paso 2:** Inmediatamente (< 30 segundos después), hacer otra en ciudad diferente
```json
{
  "id_usuario": "3c25fe57-8e1e-4a2b-9030-de0a5ee28d46",
  "monto": 100.00,
  "moneda": "MXN",
  "comercio": "Oxxo",
  "ciudad": "Guadalajara",
  "pais": "Mexico",
  "mcc": 5411
}
```

**Resultado esperado:**
```json
{
  "status": "RECHAZADO" o "REVISION_MANUAL",
  "score_riesgo": 30.0 - 70.0,
  "banderas_rojas": ["ANOMALIA_GEOGRAFICA"],
  "motivo": "...",
  "transaccion_guardada": false
}
```

**Estado:** ✅ PASS / ❌ FAIL

---

## 🖥️ PARTE 3: PRUEBAS DE INTERFAZ GRÁFICA (FRONTEND)

### **Pre-requisito:**

```bash
# Terminal separada
cd C:\fraud-detection\frontend
npm start
```

**Debe abrir automáticamente:** http://localhost:3000

---

### **Prueba 22: Carga Inicial**

**Objetivo:** Verificar que la interfaz carga correctamente.

**Pasos:**
1. Abrir http://localhost:3000

**Resultado esperado:**
- ✅ La página carga sin errores
- ✅ Se muestra el navbar con "Sistema de Detección de Fraude"
- ✅ Se muestran dos tabs: "Dashboard" y "Analizar Transacción"
- ✅ Dashboard está activo por defecto

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 23: Dashboard - Verificar Estadísticas**

**Objetivo:** Validar que el dashboard muestra datos.

**Pasos:**
1. Estar en la pestaña "Dashboard"
2. Observar las tarjetas superiores

**Resultado esperado:**
- ✅ Tarjeta "Total Usuarios": Muestra número > 0
- ✅ Tarjeta "Transacciones Totales": Muestra número > 0
- ✅ Tarjeta "Tasa de Fraude": Muestra porcentaje
- ✅ Tarjeta "Precisión del Sistema": Muestra porcentaje

**Captura de pantalla:** [ ]

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 24: Dashboard - Seleccionar Usuario**

**Objetivo:** Validar filtro de usuario.

**Pasos:**
1. Hacer scroll a "Historial de Transacciones"
2. Click en el dropdown "Selecciona un usuario"
3. Seleccionar un usuario de la lista

**Resultado esperado:**
- ✅ El dropdown muestra lista de usuarios (UUIDs)
- ✅ Al seleccionar un usuario, la tabla se llena con transacciones
- ✅ Se muestran columnas: Fecha, Monto, Moneda, Comercio, Ciudad, País, MCC

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 25: Dashboard - Tabla de Transacciones**

**Objetivo:** Verificar que la tabla muestra datos correctos.

**Pasos:**
1. Con un usuario seleccionado, observar la tabla

**Resultado esperado:**
- ✅ Se muestran transacciones (hasta 50)
- ✅ Fechas en formato legible
- ✅ Montos con 2 decimales
- ✅ Datos completos en cada fila

**Anotar cantidad de transacciones:** _______

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 26: Analizar Transacción - Formulario**

**Objetivo:** Validar que el formulario funciona.

**Pasos:**
1. Click en tab "Analizar Transacción"
2. Observar el formulario

**Resultado esperado:**
- ✅ Formulario con 7 campos:
  - Usuario (dropdown)
  - Monto (input numérico)
  - Moneda (dropdown: MXN, USD, EUR)
  - Comercio (input texto)
  - Ciudad (input texto)
  - País (input texto)
  - MCC (dropdown con categorías)
- ✅ Botón "Analizar Transacción"

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 27: Analizar Transacción - Caso APROBADO**

**Objetivo:** Probar análisis de transacción normal.

**Pasos:**
1. Llenar formulario:
   - Usuario: [Seleccionar cualquiera]
   - Monto: 150.50
   - Moneda: MXN
   - Comercio: Walmart
   - Ciudad: CDMX
   - País: Mexico
   - MCC: 5411 - Supermercados
2. Click "Analizar Transacción"

**Resultado esperado:**
- ✅ Aparece card de resultado con fondo verde
- ✅ Título: "✅ TRANSACCIÓN APROBADA"
- ✅ Score: 0%
- ✅ Mensaje: "Transacción normal según el historial..."
- ✅ Sin banderas rojas

**Captura de pantalla:** [ ]

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 28: Analizar Transacción - Caso RECHAZADO (Monto Alto)**

**Objetivo:** Probar detección de fraude por monto.

**Pasos:**
1. Llenar formulario:
   - Usuario: [El mismo de Prueba 27]
   - Monto: 15000.00
   - Moneda: MXN
   - Comercio: Walmart
   - Ciudad: CDMX
   - País: Mexico
   - MCC: 5411 - Supermercados
2. Click "Analizar Transacción"

**Resultado esperado:**
- ✅ Aparece card de resultado con fondo rojo
- ✅ Título: "❌ TRANSACCIÓN RECHAZADA"
- ✅ Score: >= 40%
- ✅ Banderas rojas visibles:
  - "ANOMALIA_MONTO (Z-Score: ...)"

**Captura de pantalla:** [ ]

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 29: Analizar Transacción - Caso RECHAZADO (Casino)**

**Objetivo:** Probar detección de categoría de riesgo.

**Pasos:**
1. Llenar formulario:
   - Usuario: [El mismo]
   - Monto: 2000.00
   - Moneda: MXN
   - Comercio: Casino Online
   - Ciudad: CDMX
   - País: Mexico
   - MCC: 7995 - Casinos/Apuestas
2. Click "Analizar Transacción"

**Resultado esperado:**
- ✅ Card rojo o amarillo (RECHAZADO o REVISION_MANUAL)
- ✅ Score: >= 30%
- ✅ Bandera: "ANOMALIA_CATEGORIA (MCC: 7995)"

**Captura de pantalla:** [ ]

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 30: Analizar Transacción - Caso REVISIÓN MANUAL**

**Objetivo:** Probar caso intermedio.

**Pasos:**
1. Llenar formulario:
   - Usuario: [El mismo]
   - Monto: 800.00
   - Moneda: USD
   - Comercio: Amazon
   - Ciudad: Nueva York
   - País: Estados Unidos
   - MCC: 5999 - Comercio en línea
2. Click "Analizar Transacción"

**Resultado esperado:**
- ✅ Card amarillo
- ✅ Título: "⚠️ REQUIERE REVISIÓN MANUAL"
- ✅ Score: entre 30% y 50%
- ✅ Banderas: ANOMALIA_GEOGRAFICA y/o ANOMALIA_MONTO

**Captura de pantalla:** [ ]

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 31: Validación de Formulario**

**Objetivo:** Verificar validaciones del formulario.

**Pasos:**
1. Intentar enviar formulario vacío
2. Intentar ingresar monto negativo
3. Intentar ingresar monto = 0

**Resultado esperado:**
- ✅ No permite enviar formulario vacío
- ✅ Muestra mensajes de error
- ✅ No permite montos <= 0

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 32: Responsividad (Mobile)**

**Objetivo:** Verificar diseño responsivo.

**Pasos:**
1. Presionar F12 (DevTools)
2. Click en ícono de dispositivo móvil
3. Seleccionar "iPhone 12 Pro"
4. Navegar por la aplicación

**Resultado esperado:**
- ✅ Dashboard se adapta a pantalla pequeña
- ✅ Formulario se adapta
- ✅ Tablas tienen scroll horizontal
- ✅ Botones son accesibles

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 33: Rendimiento de Carga**

**Objetivo:** Medir tiempo de carga.

**Pasos:**
1. Abrir DevTools (F12)
2. Ir a tab "Network"
3. Recargar página (Ctrl + R)
4. Observar tiempo total

**Resultado esperado:**
- ✅ Carga completa < 3 segundos
- ✅ Sin errores 404 o 500
- ✅ Todas las peticiones a API exitosas (200 OK)

**Tiempo de carga:** _______ segundos

**Estado:** ✅ PASS / ❌ FAIL

---

### **Prueba 34: Manejo de Errores**

**Objetivo:** Verificar comportamiento cuando la API está caída.

**Pasos:**
1. Detener el backend (Ctrl+C en terminal del backend)
2. En el frontend, intentar analizar una transacción
3. Observar comportamiento

**Resultado esperado:**
- ✅ Se muestra mensaje de error claro
- ✅ No se rompe la aplicación
- ✅ Usuario puede seguir usando el formulario

**Estado:** ✅ PASS / ❌ FAIL

---

## 🎬 PARTE 4: PRUEBAS PARA LA DEMO EN VIVO

### **Demo Script - Secuencia de Pruebas**

---

### **SETUP PRE-DEMO (1 hora antes):**

```bash
# 1. Iniciar Cassandra
docker start cassandra-fraud
# Esperar 30 segundos

# 2. Generar datos FRESCOS
cd C:\fraud-detection
venv\Scripts\activate
python src\data_generator.py

# 3. Guardar los 3 UUIDs en un archivo
notepad uuids_demo.txt
# Pegar los UUIDs ahí

# 4. Iniciar backend
python src\api.py
# Nueva terminal

# 5. Iniciar frontend
cd frontend
npm start
# Nueva terminal

# 6. Probar que todo funciona
# Ir a http://localhost:3000
# Hacer 1 análisis de prueba
```

---

### **Demo 1: Mostrar Dashboard**

**Objetivo:** Demostrar visualización de datos.

**Script:**
> "Primero, vamos a ver el dashboard donde se muestran las estadísticas generales del sistema..."

**Pasos:**
1. Abrir http://localhost:3000
2. Mostrar tarjetas superiores
3. Seleccionar un usuario del dropdown
4. Mostrar tabla de transacciones

**Puntos a mencionar:**
- "Aquí vemos el total de usuarios y transacciones"
- "Podemos ver el historial completo de cada usuario"
- "Los datos vienen directamente de Cassandra"

**Tiempo:** 1-2 minutos

---

### **Demo 2: Transacción Normal (APROBADO)**

**Objetivo:** Mostrar caso exitoso.

**Script:**
> "Ahora vamos a analizar una transacción normal, típica de este usuario..."

**Pasos:**
1. Click en tab "Analizar Transacción"
2. Llenar datos:
   ```
   Usuario: [Seleccionar uno]
   Monto: 150.50
   Moneda: MXN
   Comercio: Walmart
   Ciudad: CDMX
   País: Mexico
   MCC: 5411 - Supermercados
   ```
3. Click "Analizar Transacción"
4. Mostrar resultado verde

**Puntos a mencionar:**
- "Esta transacción se aprueba porque es consistente con el historial"
- "Monto típico, ciudad conocida, categoría normal"
- "El sistema analiza en menos de 100 milisegundos"

**Tiempo:** 1 minuto

---

### **Demo 3: Fraude por Monto Alto (RECHAZADO)**

**Objetivo:** Demostrar detección de anomalía de monto.

**Script:**
> "Ahora veamos qué pasa si intentamos una transacción de un monto inusualmente alto..."

**Pasos:**
1. Llenar datos:
   ```
   Usuario: [El mismo]
   Monto: 15000.00
   Moneda: MXN
   Comercio: Walmart
   Ciudad: CDMX
   País: Mexico
   MCC: 5411
   ```
2. Click "Analizar"
3. Mostrar resultado rojo

**Puntos a mencionar:**
- "El sistema detecta que este monto está muy por encima del promedio"
- "Usa Z-Score para medir cuánto se desvía del comportamiento normal"
- "Score de riesgo supera el 40%, por lo que se rechaza automáticamente"

**Tiempo:** 1-2 minutos

---

### **Demo 4: Fraude por Categoría de Riesgo (RECHAZADO)**

**Objetivo:** Demostrar detección de MCC peligroso.

**Script:**
> "El sistema también detecta categorías de alto riesgo, como apuestas online..."

**Pasos:**
1. Llenar datos:
   ```
   Usuario: [El mismo]
   Monto: 2000.00
   Moneda: MXN
   Comercio: Casino Online
   Ciudad: CDMX
   País: Mexico
   MCC: 7995 - Casinos/Apuestas
   ```
2. Click "Analizar"
3. Mostrar resultado

**Puntos a mencionar:**
- "Este usuario nunca ha usado esta categoría antes"
- "MCC 7995 está en la lista de alto riesgo"
- "Combinación de factores aumenta el score de riesgo"

**Tiempo:** 1-2 minutos

---

### **Demo 5: Mostrar Cassandra (OPCIONAL)**

**Objetivo:** Demostrar acceso directo a la base de datos.

**Script:**
> "Y si queremos ver los datos directamente en Cassandra..."

**Pasos:**
1. Abrir nueva terminal
2. Ejecutar:
   ```bash
   docker exec -it cassandra-fraud cqlsh
   USE finanzas;
   SELECT COUNT(*) FROM transacciones_por_usuario;
   ```

**Puntos a mencionar:**
- "Aquí estamos en CQL Shell, el lenguaje de Cassandra"
- "Podemos ver que tenemos X transacciones"
- "La velocidad de estas queries es lo que hace posible el análisis en tiempo real"

**Tiempo:** 1 minuto (si hay tiempo)

---

## 📊 RESUMEN DE RESULTADOS

### **Checklist Final:**

#### Base de Datos:
- [ ] Prueba 1: Keyspace existe
- [ ] Prueba 2: Tablas existen
- [ ] Prueba 3-4: Estructura correcta
- [ ] Prueba 5: Inserción funciona
- [ ] Prueba 6-11: Queries funcionan

#### Backend:
- [ ] Prueba 12-13: API responde
- [ ] Prueba 14: Swagger funciona
- [ ] Prueba 15-17: Endpoints de consulta funcionan
- [ ] Prueba 18-21: Análisis de fraude funciona

#### Frontend:
- [ ] Prueba 22: Interfaz carga
- [ ] Prueba 23-25: Dashboard funciona
- [ ] Prueba 26-30: Análisis funciona
- [ ] Prueba 31-34: Validaciones y errores

#### Demo:
- [ ] Setup completo
- [ ] Demos 1-4 practicadas
- [ ] UUIDs guardados
- [ ] Backup plan listo

---

## 🚨 PROBLEMAS COMUNES Y SOLUCIONES

### **Problema 1: "0 rows" en Cassandra**

**Solución:**
```bash
cd C:\fraud-detection
python src\data_generator.py
```

### **Problema 2: Backend no conecta a Cassandra**

**Solución:**
```bash
docker restart cassandra-fraud
# Esperar 30 segundos
python src\api.py
```

### **Problema 3: Frontend no carga usuarios**

**Solución:**
1. Verificar que backend esté corriendo
2. Abrir http://localhost:8000/usuarios
3. Si retorna vacío, generar datos

### **Problema 4: Puerto ocupado**

**Solución:**
```bash
# Matar proceso en puerto 8000
netstat -ano | findstr :8000
taskkill /PID [número] /F
```

---

## 📝 NOTAS FINALES

### **Para la Presentación:**

1. ✅ Imprimir este documento
2. ✅ Guardar UUIDs en notepad
3. ✅ Practicar demos 2-3 veces
4. ✅ Tener backup plan (screenshots)
5. ✅ Llevar este documento en el celular

### **Contactos de Emergencia:**

- **Documentación:** GUIA_CONSULTAS_CQL.md
- **Scripts de inicio:** iniciar_todo.bat
- **Referencia rápida:** REFERENCIA_RAPIDA_INICIO.md

---

**Última actualización:** Diciembre 2025  
**Versión:** 1.0  
**Autor:** Sistema de Detección de Fraude v2.0
