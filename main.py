# Fix para encoding UTF-8 en consola Windows (evita crashes con emojis)
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import uvicorn
import os
from app.audio_upload import app

# Configurar rutas de modelos para distribución offline
if getattr(sys, 'frozen', False):
    # Ejecutando como .exe (PyInstaller)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Ejecutando como script Python
    BASE_DIR = os.path.dirname(__file__)

# Rutas de modelos para distribución offline
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.environ["TORCH_HOME"] = os.path.join(MODELS_DIR, "torch")
os.environ["HF_HOME"] = os.path.join(MODELS_DIR, "huggingface")
os.environ["XDG_CACHE_HOME"] = MODELS_DIR

# Sistema de verificación de licencias
LICENSE_PATH = os.path.join(BASE_DIR, "license.lic")

def check_license():
    """
    Verifica la licencia al iniciar el backend.
    Retorna el estado de la licencia pero NUNCA bloquea el inicio del servidor.
    El frontend necesita acceder a los endpoints para mostrar el estado.
    """
    # Importar aquí para evitar errores si public/ no existe aún
    try:
        from public.app_state_resolver import get_app_state
    except ImportError:
        print("⚠️ Sistema de licencias no encontrado. Continuando sin verificación.")
        return None
    
    # Verificar si existe el archivo de licencia
    if not os.path.exists(LICENSE_PATH):
        print("❌ No se encontró el archivo de licencia (license.lic)")
        print("⚠️ Backend iniciará para permitir que el frontend muestre la pantalla de bloqueo.")
        return None
    
    # Obtener estado de la aplicación
    state = get_app_state(LICENSE_PATH)
    
    # Mostrar estado pero NO bloquear el servidor
    if not state["allow_usage"]:
        print(f"⚠️ {state['user_message']}")
        print(f"⚠️ [Estado: {state['state']}] - Backend iniciará para permitir acceso al frontend")
        return state
    
    # Mostrar advertencia si está por vencer
    if state["show_warning"]:
        print(f"⚠️ {state['user_message']}")
    
    # Mostrar información de licencia válida
    if state["days_remaining"] is not None:
        print(f"✅ Licencia válida - {state['days_remaining']} días restantes")
    else:
        print("✅ Licencia válida")
    
    return state

if __name__ == "__main__":
    print("🚀 Iniciando backend de transcripción...")
    
    # Verificar licencia antes de iniciar el servidor
    license_state = check_license()
    
    print("🎤 App de transcripción lista.")
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False, log_level="debug"
)