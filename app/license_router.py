"""
license_router.py
Endpoints API para consultar el estado de la licencia.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os
from pathlib import Path
import sys

# Detectar directorio base
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent

LICENSE_PATH = BASE_DIR / "license.lic"

router = APIRouter(prefix="/api/license", tags=["license"])


@router.get("/status")
def get_license_status():
    """
    Retorna el estado actual de la licencia.
    
    Returns:
        - state: ACTIVE, EXPIRING_SOON, EXPIRED, BLOCKED
        - allow_usage: bool
        - show_warning: bool
        - user_message: str
        - days_remaining: int|None
        - technical_status: str (para debugging)
    """
    try:
        from public.app_state_resolver import get_app_state
    except ImportError:
        return JSONResponse(
            status_code=200,
            content={
                "state": "BLOCKED",
                "allow_usage": False,
                "show_warning": False,
                "user_message": "Sistema de licencias no disponible",
                "days_remaining": None,
                "technical_status": "error"
            }
        )
    
    # Si no existe el archivo de licencia, retornar estado bloqueado
    if not LICENSE_PATH.exists():
        return {
            "state": "BLOCKED",
            "allow_usage": False,
            "show_warning": False,
            "user_message": "No se encontró archivo de licencia. Contacta al proveedor para obtener tu licencia.",
            "days_remaining": None,
            "technical_status": "no_license_file"
        }
    
    try:
        app_state = get_app_state(str(LICENSE_PATH))
        
        # Retornar solo campos relevantes para el frontend
        return {
            "state": app_state["state"],
            "allow_usage": app_state["allow_usage"],
            "show_warning": app_state["show_warning"],
            "user_message": app_state["user_message"],
            "days_remaining": app_state["days_remaining"],
            "technical_status": app_state["technical_status"]
        }
    except Exception as e:
        return {
            "state": "BLOCKED",
            "allow_usage": False,
            "show_warning": False,
            "user_message": "No fue posible validar el estado de la aplicación. Contacta al proveedor.",
            "days_remaining": None,
            "technical_status": f"error: {str(e)}"
        }


@router.get("/features")
def get_license_features():
    """
    Retorna las features habilitadas por la licencia.
    
    Returns:
        - features: dict con features habilitadas
        - allow_usage: bool
    """
    try:
        from public.app_state_resolver import get_app_state, get_features
    except ImportError:
        return {
            "allow_usage": False,
            "features": {}
        }
    
    # Si no existe el archivo, retornar sin features
    if not LICENSE_PATH.exists():
        return {
            "allow_usage": False,
            "features": {}
        }
    
    try:
        app_state = get_app_state(str(LICENSE_PATH))
        features = get_features(app_state)
        
        return {
            "allow_usage": app_state["allow_usage"],
            "features": features
        }
    except Exception as e:
        return {
            "allow_usage": False,
            "features": {}
        }


@router.get("/machine-id")
def get_machine_id():
    """
    Retorna el Machine ID de este equipo.
    Útil para generar nuevas licencias.
    
    Returns:
        - machine_id: str (hash SHA-256 de 64 caracteres)
    """
    try:
        from public.fingerprint import generate_machine_id
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Sistema de fingerprint no disponible"
        )
    
    try:
        machine_id = generate_machine_id()
        return {
            "machine_id": machine_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generando Machine ID: {str(e)}"
        )


@router.get("/cached-status")
def get_cached_status():
    """
    Retorna el estado cacheado de la licencia (última verificación).
    Más rápido que /status porque no verifica en tiempo real.
    
    Returns:
        - last_check: datetime de última verificación
        - state: estado cacheado
        - allow_usage: bool
        - user_message: str
        - days_remaining: int|None
    """
    try:
        from app.license_monitor import get_cached_license_state
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Monitor de licencia no disponible"
        )
    
    cached = get_cached_license_state()
    
    return {
        "last_check": cached["last_check"].isoformat() if cached["last_check"] else None,
        "state": cached["state"],
        "allow_usage": cached["allow_usage"],
        "user_message": cached["user_message"],
        "days_remaining": cached["days_remaining"]
    }
