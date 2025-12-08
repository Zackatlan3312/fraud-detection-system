# ⚡ CASOS DE PRUEBA RÁPIDOS - CHEAT SHEET

## 📋 PARA LA DEMO EN VIVO

---

## 🎯 CASOS PARA INTERFAZ GRÁFICA

### **Caso 1: Transacción APROBADA** ✅

```
Usuario: [Seleccionar del dropdown]
Monto: 150.50
Moneda: MXN
Comercio: Walmart
Ciudad: CDMX
País: Mexico
MCC: 5411 - Supermercados
```

**Resultado esperado:**
- 🟢 Card verde
- Status: APROBADO
- Score: 0%
- Sin banderas rojas

---

### **Caso 2: FRAUDE por Monto Alto** ❌

```
Usuario: [El mismo del Caso 1]
Monto: 15000.00
Moneda: MXN
Comercio: Walmart
Ciudad: CDMX
País: Mexico
MCC: 5411 - Supermercados
```

**Resultado esperado:**
- 🔴 Card rojo
- Status: RECHAZADO
- Score: ≥ 40%
- Bandera: ANOMALIA_MONTO (Z-Score alto)

---

### **Caso 3: FRAUDE por Casino** ❌

```
Usuario: [El mismo]
Monto: 2000.00
Moneda: MXN
Comercio: Casino Online
Ciudad: CDMX
País: Mexico
MCC: 7995 - Casinos/Apuestas
```

**Resultado esperado:**
- 🔴 Card rojo o 🟡 amarillo
- Status: RECHAZADO o REVISION_MANUAL
- Score: ≥ 30%
- Bandera: ANOMALIA_CATEGORIA (MCC: 7995)

---

### **Caso 4: REVISIÓN MANUAL** ⚠️

```
Usuario: [El mismo]
Monto: 800.00
Moneda: USD
Comercio: Amazon
Ciudad: Nueva York
País: Estados Unidos
MCC: 5999 - Comercio en línea
```

**Resultado esperado:**
- 🟡 Card amarillo
- Status: REVISION_MANUAL
- Score: 30-50%
- Banderas: ANOMALIA_GEOGRAFICA, posible ANOMALIA_MONTO

---

### **Caso 5: Viaje Imposible** ❌

**Paso 1:** Transacción en CDMX
```
Usuario: [Nuevo]
Monto: 100.00
Moneda: MXN
Comercio: Oxxo
Ciudad: CDMX
País: Mexico
MCC: 5411
```

**Paso 2:** INMEDIATAMENTE (<30 seg), transacción en otra ciudad
```
Usuario: [El mismo]
Monto: 100.00
Moneda: MXN
Comercio: Oxxo
Ciudad: Guadalajara
País: Mexico
MCC: 5411
```

**Resultado esperado:**
- 🔴 Card rojo
- Bandera: ANOMALIA_GEOGRAFICA
- Motivo: Viaje imposible en < 30 minutos

---

## 🗄️ CASOS PARA CASSANDRA (CQL)

### **Setup:**
```bash
docker exec -it cassandra-fraud cqlsh
USE finanzas;
```

---

### **Consulta 1: Ver estructura de tabla**

```cql
DESCRIBE TABLE transacciones_por_usuario;
```

**Explicar:**
- Partition Key: id_usuario
- Clustering Keys: timestamp DESC
- Optimizada para queries por usuario

---

### **Consulta 2: Listar usuarios**

```cql
SELECT DISTINCT id_usuario 
FROM transacciones_por_usuario 
LIMIT 5;
```

**Copiar un UUID:** _______________________________

---

### **Consulta 3: Ver transacciones (RÁPIDA)**

```cql
SELECT timestamp, monto, moneda, comercio, ciudad, pais
FROM transacciones_por_usuario
WHERE id_usuario = [PEGAR UUID]
LIMIT 10;
```

**Explicar:**
- Query en ~5ms
- Gracias a partition key
- Datos ordenados por timestamp

---

### **Consulta 4: Contar transacciones**

```cql
SELECT COUNT(*) 
FROM transacciones_por_usuario;
```

**Resultado:** Debe mostrar número total (ej: 90)

---

### **Consulta 5: Buscar por ID**

```cql
-- Obtener un ID primero
SELECT id_transaccion 
FROM transacciones_por_usuario 
WHERE id_usuario = [UUID] 
LIMIT 1;

-- Buscar en segunda tabla
SELECT * 
FROM transacciones_por_id 
WHERE id_transaccion = [PEGAR TIMEUUID];
```

**Explicar:**
- ~2ms (lookup directo)
- Por eso duplicamos datos
- Sin JOINs

---

### **Consulta 6: Query ineficiente (demostración)**

```cql
SELECT id_usuario, monto, comercio
FROM transacciones_por_usuario
WHERE monto > 1000
ALLOW FILTERING
LIMIT 10;
```

**Explicar:**
- ALLOW FILTERING = query ineficiente
- Escanea todas las particiones
- Evitar en producción

---

## 🔌 CASOS PARA API (Backend)

### **Test 1: Health Check**

```
http://localhost:8000/health
```

**Resultado:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

### **Test 2: Listar usuarios**

```
http://localhost:8000/usuarios
```

**Resultado:**
```json
{
  "total_usuarios": 3,
  "usuarios": ["uuid1", "uuid2", "uuid3"]
}
```

**Copiar un UUID:** _______________________________

---

### **Test 3: Historial de usuario**

```
http://localhost:8000/historial/[PEGAR UUID]?limite=10
```

**Resultado:** Lista de 10 transacciones

---

### **Test 4: Estadísticas**

```
http://localhost:8000/estadisticas/[PEGAR UUID]
```

**Resultado:**
```json
{
  "total_transacciones": 30,
  "monto_total": 4500.50,
  "monto_promedio": 150.02,
  "ciudades_frecuentes": [...],
  "comercios_frecuentes": [...]
}
```

---

### **Test 5: API Docs (Swagger)**

```
http://localhost:8000/docs
```

**Mostrar:**
- Interfaz interactiva
- Todos los endpoints
- Probar POST /analizar-transaccion

---

## 📊 DATOS DE REFERENCIA

### **Códigos MCC Comunes:**

| MCC  | Descripción         | Riesgo |
|------|---------------------|--------|
| 5411 | Supermercados       | Bajo   |
| 5812 | Restaurantes        | Bajo   |
| 5541 | Gasolineras         | Bajo   |
| 5999 | Comercio en línea   | Medio  |
| 7995 | Casinos/Apuestas    | **ALTO** |

---

### **UUIDs para Guardar:**

```
Usuario 1: _________________________________
Usuario 2: _________________________________
Usuario 3: _________________________________
```

---

### **Montos Típicos vs Fraude:**

| Tipo | Monto |
|------|-------|
| Normal | $20 - $500 |
| Sospechoso | $500 - $2,000 |
| Fraude | $5,000+ |

---

## 🎬 SECUENCIA DE DEMO (5 MINUTOS)

### **Minuto 1: Introducción**
- Abrir http://localhost:3000
- Mostrar dashboard
- Explicar estadísticas

### **Minuto 2: Caso Aprobado**
- Tab "Analizar Transacción"
- Llenar Caso 1
- Mostrar resultado verde

### **Minuto 3: Caso Fraude Monto**
- Llenar Caso 2
- Mostrar resultado rojo
- Explicar Z-Score

### **Minuto 4: Caso Fraude Casino**
- Llenar Caso 3
- Mostrar detección de MCC

### **Minuto 5: Mostrar Cassandra (opcional)**
- Terminal: docker exec -it cassandra-fraud cqlsh
- USE finanzas;
- SELECT COUNT(*)...
- Explicar velocidad

---

## 🚨 TROUBLESHOOTING RÁPIDO

### **No hay datos:**
```bash
python src\data_generator.py
```

### **Backend no responde:**
```bash
python src\api.py
```

### **Frontend no carga:**
```bash
cd frontend
npm start
```

### **Cassandra no conecta:**
```bash
docker restart cassandra-fraud
# Esperar 30 segundos
```

---

## 📱 PARA LLEVAR EN EL CELULAR

```
INICIO RÁPIDO
=============
1. docker start cassandra-fraud
2. python src\api.py
3. cd frontend && npm start

URLS
====
Frontend: localhost:3000
Backend: localhost:8000
Docs: localhost:8000/docs

CASSANDRA
=========
docker exec -it cassandra-fraud cqlsh
USE finanzas;
SELECT COUNT(*) FROM transacciones_por_usuario;

CASO DEMO
=========
Monto: 15000
-> RECHAZADO (Monto alto)

Monto: 2000, MCC: 7995
-> RECHAZADO (Casino)
```

---

**🎯 IMPRIME ESTE DOCUMENTO Y TENLO A MANO DURANTE LA PRESENTACIÓN**
