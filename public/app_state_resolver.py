"""
app_state_resolver.py

CAPA 5 - Degradación Silenciosa
Orquesta la experiencia de usuario según el estado técnico de la licencia.

NO es seguridad criptográfica.
Es seguridad psicológica + de producto.

Objetivo:
- No dar pistas a atacantes
- Guiar al usuario legítimo a renovar
- Hacer incómodo/confuso el crack
"""

from typing import Dict, Tuple
from datetime import datetime
from .license_verifier import verify_license, read_license_file


# Estados de experiencia de usuario (UX)
class AppState:
    ACTIVE = "ACTIVE"                  # Membresía activa - App completa
    EXPIRING_SOON = "EXPIRING_SOON"   # Por vencer - App completa + avisos
    EXPIRED = "EXPIRED"               # Vencida - Bloqueada
    BLOCKED = "BLOCKED"               # Hostil/sospechoso - Bloqueada


# Configuración de umbrales
EXPIRING_THRESHOLD_DAYS = 3  # Días antes de expirar para mostrar avisos


def calculate_days_remaining(expires_at_str: str) -> int:
    """
    Calcula días restantes hasta expiración.
    
    Args:
        expires_at_str: Fecha ISO 8601 de expiración
        
    Returns:
        int: Días restantes (puede ser negativo si ya expiró)
    """
    try:
        expires_at = datetime.fromisoformat(expires_at_str)
        now = datetime.now()
        delta = expires_at - now
        return delta.days
    except Exception:
        return -999  # Error → considerar expirado


def get_app_state(license_path: str) -> Dict:
    """
    Resuelve el estado de la aplicación según la licencia.
    
    Traduce estados técnicos a estados de experiencia:
    - valid → ACTIVE o EXPIRING_SOON (según días restantes)
    - expired → EXPIRED
    - invalid/manipulated/clock_rollback → BLOCKED
    
    Args:
        license_path: Ruta al archivo de licencia
        
    Returns:
        dict con:
        - state: str (ACTIVE, EXPIRING_SOON, EXPIRED, BLOCKED)
        - allow_usage: bool (True si puede usar la app)
        - show_warning: bool (True si mostrar aviso)
        - user_message: str (mensaje para el usuario)
        - days_remaining: int|None (días hasta expiración, solo si válida)
        - features: dict|None (features habilitadas, solo si válida)
        - technical_status: str (estado técnico original, para logs)
    """
    
    # Verificar licencia (estado técnico)
    technical_status, technical_reason = verify_license(license_path)
    
    result = {
        "state": None,
        "allow_usage": False,
        "show_warning": False,
        "user_message": "",
        "days_remaining": None,
        "features": None,
        "technical_status": technical_status,  # Para logs internos
    }
    
    # 1️⃣ Licencia válida → Calcular días restantes
    if technical_status == "valid":
        try:
            license_data = read_license_file(license_path)
            expires_at = license_data.get("expires_at")
            days_remaining = calculate_days_remaining(expires_at)
            
            result["days_remaining"] = days_remaining
            result["features"] = license_data.get("features", {})
            
            # 2️⃣ Membresía por vencer (EXPIRING_SOON)
            if 0 <= days_remaining <= EXPIRING_THRESHOLD_DAYS:
                result["state"] = AppState.EXPIRING_SOON
                result["allow_usage"] = True
                result["show_warning"] = True
                
                if days_remaining == 0:
                    result["user_message"] = (
                        "Tu membresía expira hoy. "
                        "Contacta al proveedor para renovar."
                    )
                elif days_remaining == 1:
                    result["user_message"] = (
                        "Tu membresía expira mañana. "
                        "Contacta al proveedor para renovar."
                    )
                else:
                    result["user_message"] = (
                        f"Tu membresía expira en {days_remaining} días. "
                        f"Contacta al proveedor para renovar."
                    )
            
            # 1️⃣ Membresía activa (ACTIVE)
            else:
                result["state"] = AppState.ACTIVE
                result["allow_usage"] = True
                result["show_warning"] = False
                result["user_message"] = "Aplicación lista"
        
        except Exception:
            # Error leyendo licencia válida → tratar como bloqueada
            result["state"] = AppState.BLOCKED
            result["allow_usage"] = False
            result["show_warning"] = False
            result["user_message"] = (
                "No fue posible validar el estado de la aplicación. "
                "Contacta al proveedor."
            )
    
    # 3️⃣ Membresía vencida (EXPIRED)
    elif technical_status == "expired":
        result["state"] = AppState.EXPIRED
        result["allow_usage"] = False
        result["show_warning"] = False
        result["user_message"] = (
            "Tu membresía ha expirado. "
            "Contacta al proveedor para renovar y continuar usando la aplicación."
        )
    
    # 4️⃣ Estados hostiles o sospechosos (BLOCKED)
    # invalid, manipulated, clock_rollback
    else:
        result["state"] = AppState.BLOCKED
        result["allow_usage"] = False
        result["show_warning"] = False
        
        # ⚠️ NO DAR PISTAS - Mensaje genérico
        result["user_message"] = (
            "No fue posible validar el estado de la aplicación. "
            "Contacta al proveedor."
        )
        
        # NUNCA decir:
        # - "Firma inválida"
        # - "license_hash incorrecto"
        # - "reloj modificado"
        # - "machine_id no coincide"
        # Eso es regalar el mapa del tesoro 🗺️
    
    return result


def should_block_app(app_state: Dict) -> bool:
    """
    Determina si la app debe bloquearse.
    
    Args:
        app_state: Dict retornado por get_app_state()
        
    Returns:
        bool: True si debe bloquear, False si puede continuar
    """
    return not app_state["allow_usage"]


def get_user_message(app_state: Dict) -> str:
    """
    Obtiene el mensaje a mostrar al usuario.
    
    Args:
        app_state: Dict retornado por get_app_state()
        
    Returns:
        str: Mensaje para mostrar al usuario
    """
    return app_state["user_message"]


def get_features(app_state: Dict) -> Dict:
    """
    Obtiene features habilitadas (solo si licencia válida).
    
    Args:
        app_state: Dict retornado por get_app_state()
        
    Returns:
        dict: Features habilitadas o {} si no válida
    """
    return app_state.get("features") or {}


# Ejemplo de uso
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python app_state_resolver.py <ruta_license.lic>")
        exit(1)
    
    license_file = sys.argv[1]
    
    print("🔍 Resolviendo estado de aplicación...")
    print(f"📄 Licencia: {license_file}\n")
    
    app_state = get_app_state(license_file)
    
    print(f"Estado UX: {app_state['state']}")
    print(f"Permitir uso: {app_state['allow_usage']}")
    print(f"Mostrar aviso: {app_state['show_warning']}")
    print(f"Mensaje: {app_state['user_message']}")
    
    if app_state['days_remaining'] is not None:
        print(f"Días restantes: {app_state['days_remaining']}")
    
    if app_state['features']:
        print(f"Features: {app_state['features']}")
    
    print(f"\n[DEBUG] Estado técnico: {app_state['technical_status']}")
    
    # Decisión
    if should_block_app(app_state):
        print("\n🚫 APLICACIÓN BLOQUEADA")
        exit(1)
    else:
        print("\n✅ APLICACIÓN PERMITIDA")
        exit(0)
