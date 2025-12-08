# 🔍 ANÁLISIS DEL PROYECTO - Sistema de Detección de Fraude

## 📋 ESTADO ACTUAL

### ✅ Archivos Existentes
```
fraud-detection/
├── src/
│   ├── __init__.py
│   ├── api.py
│   ├── database.py
│   ├── fraud_detector.py
│   └── data_generator.py
├── frontend/
│   ├── src/
│   │   ├── Dashboard.jsx
│   │   ├── Navbar.jsx
│   │   └── TransactionAnalyzer.jsx
│   ├── package.json
│   ├── postcss.config.js
│   └── tailwind.config.js
├── requirements.txt
└── README.md
```

---

## 🚨 PROBLEMAS IDENTIFICADOS

### 1. **CRÍTICO: Archivo config.py FALTANTE**
**Archivos afectados:**
- `api.py` (línea 13): `from config.config import API_HOST, API_PORT`
- `fraud_detector.py` (línea 10): `from config.config import HISTORIAL_LIMITE, Z_SCORE_UMBRAL, TIEMPO_MINIMO_VIAJE`

**Solución:** Crear el archivo `config/config.py` con las constantes necesarias.

---

### 2. **CRÍTICO: Dependencias Faltantes en requirements.txt**
**Dependencias necesarias NO incluidas:**
- `fastapi` - Framework web para la API
- `uvicorn` - Servidor ASGI para FastAPI
- `cassandra-driver` - Cliente de Apache Cassandra
- `pydantic` - Validación de datos para FastAPI

**requirements.txt actual:** Solo tiene dependencias de GUI desktop (PyQt5, pygame, etc.) que NO son necesarias para este proyecto web.

---

### 3. **ERROR: Estructura de Directorios Incorrecta**
**Problema:** Los archivos están en la raíz en lugar de estar organizados.

**Estructura actual:**
```
/mnt/project/
├── api.py          ❌ Debería estar en src/
├── database.py     ❌ Debería estar en src/
├── fraud_detector.py ❌ Debería estar en src/
├── data_generator.py ❌ Debería estar en src/
├── Dashboard.jsx   ❌ Debería estar en frontend/src/
├── Navbar.jsx      ❌ Debería estar en frontend/src/
└── TransactionAnalyzer.jsx ❌ Debería estar en frontend/src/
```

---

### 4. **Frontend Incompleto**
**Archivos faltantes:**
- `frontend/src/App.js` - Componente principal
- `frontend/src/index.js` - Punto de entrada
- `frontend/src/index.css` - Estilos globales
- `frontend/public/index.html` - HTML base

---

### 5. **Base de Datos: Tablas NO Creadas**
El README menciona "Crear las tablas en Cassandra (ver documentación)" pero:
- ❌ No existe documentación sobre cómo crear las tablas
- ❌ No hay scripts SQL/CQL
- ❌ No hay script de inicialización automática

**Tablas necesarias (según database.py):**
```cql
-- Keyspace
CREATE KEYSPACE IF NOT EXISTS finanzas 
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

-- Tabla 1: Transacciones por usuario (para historial)
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

-- Tabla 2: Transacciones por ID (para búsqueda directa)
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

---

### 6. **Problemas de Código en database.py**

**Líneas 6-11:** Workaround innecesario y peligroso
```python
# Fix para Python 3.12
import sys
try:
    import asyncore
except ImportError:
    import pyasyncore as asyncore
    sys.modules['asyncore'] = asyncore
```
**Problema:** `asyncore` está deprecated desde Python 3.6. Este workaround puede causar problemas.

---

### 7. **TransactionAnalyzer.jsx: Hardcoded User IDs**
```javascript
const TransactionAnalyzer = ({ userIds }) => {
  const [formData, setFormData] = useState({
    id_usuario: userIds[0] || '', // ❌ ¿De dónde vienen los userIds?
```

**Problema:** El componente espera recibir `userIds` como prop, pero no hay integración con el backend para obtener usuarios.

---

## 🎯 PRIORIDADES DE CORRECCIÓN

### **Fase 1: Base y Configuración** (CRÍTICO)
1. ✅ Crear estructura de directorios correcta
2. ✅ Crear `config/config.py`
3. ✅ Corregir `requirements.txt`
4. ✅ Crear script de inicialización de base de datos

### **Fase 2: Backend**
5. ✅ Reorganizar archivos Python
6. ✅ Agregar endpoint para obtener lista de usuarios
7. ✅ Mejorar manejo de errores

### **Fase 3: Frontend**
8. ✅ Crear archivos faltantes de React
9. ✅ Integrar componentes
10. ✅ Conectar con backend

### **Fase 4: Testing y Documentación**
11. ✅ Crear documentación completa
12. ✅ Agregar scripts de inicio automático
13. ✅ Crear guía de deployment

---

## 📊 DIAGRAMA DE ARQUITECTURA ACTUAL

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Dashboard   │  │   Navbar     │  │ TransactionAnalyzer │
│  └──────────────┘  └──────────────┘  └─────────────────┘   │
│                            │                                 │
│                            ↓                                 │
│                    HTTP REST API                             │
└─────────────────────────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   api.py     │→ │fraud_detector│→ │   database.py   │   │
│  │ (Endpoints)  │  │  (Análisis)  │  │  (Cassandra)    │   │
│  └──────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│               APACHE CASSANDRA (NoSQL DB)                    │
│  ┌────────────────────────────────────────────────────┐     │
│  │  transacciones_por_usuario (historial por user)    │     │
│  │  transacciones_por_id (búsqueda por ID)            │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 ALGORITMO DE DETECCIÓN DE FRAUDE

### 4 Reglas Implementadas:

1. **Anomalía Geográfica** (+30% riesgo)
   - Detecta si la ciudad es diferente a la última transacción
   - Y el tiempo transcurrido es menor a `TIEMPO_MINIMO_VIAJE`

2. **Anomalía de Monto** (+40% riesgo)
   - Usa Z-Score para detectar montos anormalmente altos
   - Z-Score > `Z_SCORE_UMBRAL` (típicamente 3.0)

3. **Anomalía de Frecuencia** (+20% riesgo)
   - Detecta transacciones en ráfaga
   - Si transacciones/hora > 5× promedio

4. **Anomalía de Categoría MCC** (+10% riesgo)
   - Detecta categorías de alto riesgo nunca usadas antes
   - MCCs riesgo: 7995 (apuestas), 5993 (cigarros), etc.

### Decisión Final:
- **Score ≥ 50%** → RECHAZADO
- **30% ≤ Score < 50%** → REVISIÓN MANUAL
- **Score < 30%** → APROBADO

---

## 📝 PRÓXIMOS PASOS

1. **Crear estructura de directorios correcta**
2. **Implementar archivos faltantes**
3. **Corregir dependencias**
4. **Agregar scripts de automatización**
5. **Crear documentación de usuario**
