"""
license_monitor.py
Monitoreo periódico de licencia en background.
"""
import asyncio
import os
from pathlib import Path
import sys
from datetime import datetime

# Detectar directorio base
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent

LICENSE_PATH = BASE_DIR / "license.lic"

# Configuración
CHECK_INTERVAL_HOURS = 6  # Verificar cada 6 horas
CHECK_INTERVAL_SECONDS = CHECK_INTERVAL_HOURS * 3600

# Estado global de la licencia (cache)
_license_state = {
    "last_check": None,
    "state": None,
    "allow_usage": True,
    "user_message": "",
    "days_remaining": None
}


def get_cached_license_state():
    """Retorna el estado cacheado de la licencia."""
    return _license_state.copy()


async def check_license_background():
    """
    Tarea en background que verifica la licencia periódicamente.
    Se ejecuta cada CHECK_INTERVAL_HOURS horas.
    """
    global _license_state
    
    print(f"🔄 Monitor de licencia iniciado (cada {CHECK_INTERVAL_HOURS}h)")
    
    while True:
        try:
            from public.app_state_resolver import get_app_state
            
            if LICENSE_PATH.exists():
                state = get_app_state(str(LICENSE_PATH))
                
                # Actualizar estado global
                _license_state["last_check"] = datetime.now()
                _license_state["state"] = state["state"]
                _license_state["allow_usage"] = state["allow_usage"]
                _license_state["user_message"] = state["user_message"]
                _license_state["days_remaining"] = state["days_remaining"]
                
                # Log si hay cambios importantes
                if not state["allow_usage"]:
                    print(f"⚠️ LICENCIA BLOQUEADA: {state['user_message']}")
                elif state["show_warning"]:
                    print(f"⚠️ {state['user_message']}")
                
        except Exception as e:
            print(f"❌ Error en verificación periódica de licencia: {e}")
        
        # Esperar hasta la siguiente verificación
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


def start_license_monitor():
    """
    Inicia el monitor de licencia en background.
    Debe llamarse al iniciar la app FastAPI.
    """
    asyncio.create_task(check_license_background())
