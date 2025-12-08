# ⚡ Guía de Instalación Rápida

## 📋 Pre-requisitos

Antes de comenzar, asegúrate de tener instalado:

- [ ] Python 3.8 o superior
- [ ] Node.js 14 o superior
- [ ] Docker
- [ ] Git

### Verificar instalaciones

```bash
python --version    # Debe mostrar 3.8+
node --version      # Debe mostrar 14+
npm --version       # Debe mostrar 6+
docker --version    # Debe mostrar 20+
```

---

## 🚀 Instalación en 5 Minutos

### 1️⃣ Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/fraud-detection.git
cd fraud-detection
```

### 2️⃣ Iniciar Cassandra

```bash
docker run --name cassandra-fraud -p 9042:9042 -d cassandra:latest
```

**⏱ Espera 30 segundos** mientras Cassandra se inicializa.

### 3️⃣ Configurar el Backend

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 4️⃣ Inicializar Base de Datos

```bash
python scripts/init_database.py
```

**✅ Salida esperada:**
```
✓ Cassandra está disponible
✓ Keyspace 'finanzas' creado exitosamente
✓ Todas las tablas necesarias están creadas
✓ INICIALIZACIÓN COMPLETADA EXITOSAMENTE
```

### 5️⃣ Generar Datos de Prueba

```bash
python src/data_generator.py
```

Esto creará 3 usuarios con transacciones de ejemplo.
**Guarda los UUIDs** que se muestran al final.

### 6️⃣ Configurar el Frontend

```bash
cd frontend
npm install
```

---

## ▶️ Iniciar el Sistema

### Opción A: Script Automático (Recomendado)

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
./start.sh
```

### Opción B: Manual

**Terminal 1 - Backend:**
```bash
python src/api.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

---

## 🎯 Acceder a la Aplicación

Una vez iniciado:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs

---

## 🧪 Probar el Sistema

1. Abre http://localhost:3000
2. Ve a la pestaña **"Analizar Transacción"**
3. Selecciona un usuario del dropdown
4. Llena el formulario:
   - Monto: `150.00`
   - Moneda: `MXN`
   - Comercio: `Walmart`
   - Ciudad: `CDMX`
   - País: `Mexico`
   - MCC: `5411`
5. Haz clic en **"Analizar Transacción"**
6. Observa el resultado: ✅ **APROBADO**

### Probar Fraude

Ahora prueba con valores sospechosos:
- Monto: `15000.00` (muy alto)
- Ciudad: `Paris` (ubicación extraña)
- MCC: `7995` (casino - alto riesgo)

Deberías ver: ⚠️ **RECHAZADO** o **REVISIÓN MANUAL**

---

## 🛑 Detener el Sistema

### Si usaste el script:
- **Windows**: Cierra las ventanas de cmd
- **Linux/Mac**: Presiona `Ctrl+C`

### Si iniciaste manualmente:
- Presiona `Ctrl+C` en ambas terminales

### Detener Cassandra:
```bash
docker stop cassandra-fraud
```

---

## 🐛 Problemas Comunes

### "Cannot connect to Cassandra"

```bash
# Verificar que esté corriendo
docker ps

# Si no aparece, iniciarlo
docker start cassandra-fraud

# Esperar 30 segundos
```

### "Port 8000 already in use"

```bash
# Encontrar qué proceso usa el puerto
# Windows:
netstat -ano | findstr :8000
# Linux/Mac:
lsof -i :8000

# Matar el proceso o cambiar el puerto en config/config.py
```

### "Module not found"

```bash
# Asegúrate de estar en la raíz del proyecto
pwd  # o cd en Windows

# Verifica que exista venv/
ls venv/  # o dir venv\ en Windows

# Reactiva el entorno virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

---

## 📚 Siguiente Paso

Lee el **README.md** completo para:
- Entender la arquitectura
- Aprender sobre el algoritmo de detección
- Ver la documentación completa de la API
- Contribuir al proyecto

---

## ✅ Checklist de Verificación

Antes de reportar un problema, verifica:

- [ ] Docker está instalado y corriendo
- [ ] Cassandra está corriendo (`docker ps`)
- [ ] Entorno virtual está activado
- [ ] Todas las dependencias están instaladas
- [ ] La base de datos fue inicializada
- [ ] No hay conflictos de puertos (8000, 3000, 9042)
- [ ] Firewall permite las conexiones locales

---

**¿Todo funcionó?** ¡Genial! 🎉

**¿Problemas?** Abre un issue en GitHub o consulta el README completo.
