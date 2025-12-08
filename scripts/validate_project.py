"""
Script de validación del proyecto
Verifica que todos los archivos necesarios existan y estén correctos
"""

import os
import sys
from pathlib import Path


class Colors:
    """Colores para output en terminal"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")


def print_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")


def check_file_exists(filepath, required=True):
    """Verifica si un archivo existe"""
    path = Path(filepath)
    exists = path.exists()
    
    if exists:
        print_success(f"{filepath}")
        return True
    else:
        if required:
            print_error(f"{filepath} (FALTANTE - REQUERIDO)")
        else:
            print_warning(f"{filepath} (opcional)")
        return False


def check_python_version():
    """Verifica la versión de Python"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} (Requiere 3.8+)")
        return False


def check_dependencies():
    """Verifica que las dependencias principales estén instaladas"""
    dependencies = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'cassandra': 'Cassandra Driver',
        'numpy': 'NumPy',
        'pydantic': 'Pydantic'
    }
    
    all_installed = True
    for module, name in dependencies.items():
        try:
            __import__(module)
            print_success(f"{name}")
        except ImportError:
            print_error(f"{name} (NO INSTALADO)")
            all_installed = False
    
    return all_installed


def main():
    """Función principal de validación"""
    print("\n" + "="*60)
    print("VALIDACIÓN DEL PROYECTO - Sistema de Detección de Fraude")
    print("="*60 + "\n")
    
    all_ok = True
    
    # 1. Verificar versión de Python
    print("1️⃣  Verificando Python...")
    if not check_python_version():
        all_ok = False
    print()
    
    # 2. Verificar estructura de directorios
    print("2️⃣  Verificando estructura de directorios...")
    directories = [
        'config',
        'src',
        'frontend',
        'frontend/src',
        'frontend/src/components',
        'frontend/public',
        'scripts',
        'docs'
    ]
    
    for directory in directories:
        if not Path(directory).is_dir():
            print_error(f"{directory}/ (FALTANTE)")
            all_ok = False
        else:
            print_success(f"{directory}/")
    print()
    
    # 3. Verificar archivos del backend
    print("3️⃣  Verificando archivos del backend...")
    backend_files = [
        'config/__init__.py',
        'config/config.py',
        'src/__init__.py',
        'src/api.py',
        'src/database.py',
        'src/fraud_detector.py',
        'src/data_generator.py',
        'scripts/init_database.py',
        'requirements.txt'
    ]
    
    for filepath in backend_files:
        if not check_file_exists(filepath):
            all_ok = False
    print()
    
    # 4. Verificar archivos del frontend
    print("4️⃣  Verificando archivos del frontend...")
    frontend_files = [
        'frontend/package.json',
        'frontend/tailwind.config.js',
        'frontend/postcss.config.js',
        'frontend/public/index.html',
        'frontend/src/App.js',
        'frontend/src/index.js',
        'frontend/src/index.css',
        'frontend/src/components/Dashboard.jsx',
        'frontend/src/components/Navbar.jsx',
        'frontend/src/components/TransactionAnalyzer.jsx'
    ]
    
    for filepath in frontend_files:
        if not check_file_exists(filepath):
            all_ok = False
    print()
    
    # 5. Verificar documentación
    print("5️⃣  Verificando documentación...")
    doc_files = [
        'README.md',
        'docs/INSTALACION_RAPIDA.md',
        'docs/ANALISIS_PROYECTO.md',
        '.gitignore'
    ]
    
    for filepath in doc_files:
        check_file_exists(filepath, required=False)
    print()
    
    # 6. Verificar scripts de inicio
    print("6️⃣  Verificando scripts de inicio...")
    script_files = [
        'start.sh',
        'start.bat'
    ]
    
    for filepath in script_files:
        check_file_exists(filepath, required=False)
    print()
    
    # 7. Verificar dependencias Python (si está en venv)
    if Path('venv').exists():
        print("7️⃣  Verificando dependencias Python...")
        if not check_dependencies():
            all_ok = False
            print_warning("Algunas dependencias no están instaladas")
            print_info("Ejecuta: pip install -r requirements.txt")
        print()
    else:
        print("7️⃣  Entorno virtual no encontrado...")
        print_warning("Se recomienda crear un entorno virtual")
        print_info("Ejecuta: python -m venv venv")
        print()
    
    # Resultado final
    print("="*60)
    if all_ok:
        print_success("✓ VALIDACIÓN COMPLETADA - Todos los archivos necesarios están presentes")
        print()
        print_info("Siguiente paso:")
        print("  1. Iniciar Cassandra: docker run --name cassandra-fraud -p 9042:9042 -d cassandra:latest")
        print("  2. Inicializar BD: python scripts/init_database.py")
        print("  3. Generar datos: python src/data_generator.py")
        print("  4. Iniciar sistema: ./start.sh (o start.bat en Windows)")
    else:
        print_error("✗ VALIDACIÓN FALLIDA - Faltan archivos necesarios")
        print()
        print_info("Revisa los errores arriba y asegúrate de tener todos los archivos")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
