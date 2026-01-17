def verify_license_hash(payload: dict) -> bool:
    """
    Verifica que el campo license_hash sea igual al SHA-256 del payload canónico sin el propio license_hash.
    """
    import copy
    import json
    import hashlib
    import base64
    if 'license_hash' not in payload:
        return False
    license_hash = payload['license_hash']
    # Copiar y eliminar license_hash
    payload_no_hash = copy.deepcopy(payload)
    del payload_no_hash['license_hash']
    # Canonicalizar JSON
    canonical = json.dumps(payload_no_hash, sort_keys=True, separators=(",", ":"))
    hash_bytes = hashlib.sha256(canonical.encode('utf-8')).digest()
    calc_hash = base64.b64encode(hash_bytes).decode("ascii")
    return license_hash == calc_hash
SUPPORTED_LICENSE_VERSION = 1
"""
license_verifier.py
Valida licencias offline firmadas digitalmente usando Ed25519.
- Verifica firma digital con public.key
- Valida machine_id, fechas y retroceso de reloj
- Devuelve estado técnico y motivo
"""
import json
import os
import hashlib
from datetime import datetime
from typing import Tuple, Dict
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from .fingerprint import generate_machine_id
import sys

LICENSE_STATUS = {
    'valid': 'Licencia válida',
    'invalid': 'Licencia inválida',
    'expired': 'Licencia expirada',
    'manipulated': 'Licencia manipulada',
    'clock_rollback': 'Retroceso de reloj detectado',
}

def get_resource_path(relative_path):
    """Obtiene la ruta correcta tanto en desarrollo como en ejecutable PyInstaller."""
    if getattr(sys, 'frozen', False):
        # Ejecutable empaquetado con PyInstaller
        base_path = sys._MEIPASS
    else:
        # Desarrollo - ruta del módulo
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# Rutas que funcionan tanto en desarrollo como en .exe
PUBLIC_KEY_PATH = get_resource_path('public/keys/public.key')

# Para data dir, usar directorio del ejecutable (no _MEIPASS temporal)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
LAST_RUN_FILE = os.path.join(DATA_DIR, '.last_run')


def load_public_key(path: str = PUBLIC_KEY_PATH) -> Ed25519PublicKey:
    with open(path, 'rb') as f:
        key_data = f.read()
    return Ed25519PublicKey.from_public_bytes(key_data)


def read_license_file(license_path: str) -> Dict:
    with open(license_path, 'r', encoding='utf-8') as f:
        lic = json.load(f)
    return lic


def verify_signature_raw(payload: dict, signature_b64: str, public_key: Ed25519PublicKey) -> bool:
    import base64
    payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode('utf-8')
    try:
        signature = base64.b64decode(signature_b64)
        public_key.verify(signature, payload_bytes)
        return True
    except Exception:
        return False


def check_clock_rollback(last_run_path: str, now: datetime) -> bool:
    if not os.path.exists(last_run_path):
        return False
    try:
        with open(last_run_path, 'r') as f:
            content = f.read().strip()
        # Esperado: timestamp|hash
        parts = content.split('|')
        if len(parts) != 2:
            return True  # manipulación
        last_run_str, last_hash = parts
        last_run = datetime.fromisoformat(last_run_str)
        # Recalcular hash
        local_id = generate_machine_id()
        expected_hash = hashlib.sha256((last_run_str + local_id).encode('utf-8')).hexdigest()
        if last_hash != expected_hash:
            return True  # manipulación
        return now < last_run
    except Exception:
        return True  # ante error, bloquear


def update_last_run(last_run_path: str, now: datetime):
    local_id = generate_machine_id()
    timestamp = now.isoformat()
    hash_val = hashlib.sha256((timestamp + local_id).encode('utf-8')).hexdigest()
    with open(last_run_path, 'w') as f:
        f.write(f'{timestamp}|{hash_val}')


def verify_structure(lic: dict) -> dict:
    required_fields = ('machine_id', 'issued_at', 'not_before', 'expires_at', 'features', 'license_hash', 'signature')
    for field in required_fields:
        if field not in lic:
            return {'status': 'manipulated', 'reason': f'Falta campo: {field}'}
    return {'status': 'ok'}

def verify_version(lic: dict) -> dict:
    license_version = lic.get('license_version', None)
    if license_version is None:
        return {'status': 'manipulated', 'reason': 'Falta campo: license_version'}
    if not isinstance(license_version, int):
        return {'status': 'manipulated', 'reason': 'license_version no es entero'}
    if license_version > SUPPORTED_LICENSE_VERSION:
        return {'status': 'manipulated', 'reason': 'Versión de licencia no soportada'}
    return {'status': 'ok'}

def verify_integrity(payload: dict) -> dict:
    if not verify_license_hash(payload):
        return {'status': 'manipulated', 'reason': 'license_hash inválido o manipulado'}
    return {'status': 'ok'}

def verify_signature(payload: dict, signature: str, public_key_path: str = PUBLIC_KEY_PATH) -> dict:
    try:
        public_key = load_public_key(public_key_path)
    except Exception as e:
        return {'status': 'manipulated', 'reason': f'Error cargando public.key: {e}'}
    if not verify_signature_raw(payload, signature, public_key):
        return {'status': 'manipulated', 'reason': 'Firma digital inválida'}
    return {'status': 'ok'}

def verify_machine_binding(payload: dict) -> dict:
    local_id = generate_machine_id()
    if payload['machine_id'] != local_id:
        return {'status': 'invalid', 'reason': 'machine_id no coincide'}
    return {'status': 'ok'}

def verify_time_window(payload: dict, now: datetime = None) -> dict:
    if now is None:
        now = datetime.now()
    try:
        issued = datetime.fromisoformat(payload['issued_at'])
        not_before = datetime.fromisoformat(payload['not_before'])
        expires = datetime.fromisoformat(payload['expires_at'])
    except Exception:
        return {'status': 'manipulated', 'reason': 'Fechas inválidas en licencia'}
    if now < not_before:
        return {'status': 'invalid', 'reason': 'Licencia aún no válida (not_before futuro)'}
    if now < issued:
        return {'status': 'invalid', 'reason': 'Licencia aún no válida (issued_at futuro)'}
    if now > expires:
        return {'status': 'expired', 'reason': 'Licencia expirada'}
    return {'status': 'ok'}

def verify_clock_rollback(now: datetime = None) -> dict:
    if now is None:
        now = datetime.now()
    if check_clock_rollback(LAST_RUN_FILE, now):
        return {'status': 'clock_rollback', 'reason': 'Retroceso de reloj detectado'}
    return {'status': 'ok'}

def verify_license(license_path: str, public_key_path: str = PUBLIC_KEY_PATH) -> Tuple[str, str]:
    now = datetime.now()
    try:
        lic = read_license_file(license_path)
    except Exception as e:
        return 'manipulated', f'Error leyendo licencia: {e}'

    # Coordinador: ejecuta todas las verificaciones y retorna el primer error
    result = verify_version(lic)
    if result['status'] != 'ok':
        return result['status'], result['reason']
    result = verify_structure(lic)
    if result['status'] != 'ok':
        return result['status'], result['reason']
    payload = {k: v for k, v in lic.items() if k != 'signature'}
    signature = lic['signature']
    result = verify_integrity(payload)
    if result['status'] != 'ok':
        return result['status'], result['reason']
    result = verify_signature(payload, signature, public_key_path)
    if result['status'] != 'ok':
        return result['status'], result['reason']
    result = verify_machine_binding(payload)
    if result['status'] != 'ok':
        return result['status'], result['reason']
    result = verify_time_window(payload, now)
    if result['status'] != 'ok':
        return result['status'], result['reason']
    result = verify_clock_rollback(now)
    if result['status'] != 'ok':
        return result['status'], result['reason']
    try:
        update_last_run(LAST_RUN_FILE, now)
    except Exception:
        pass  # No es crítico
    return 'valid', 'Licencia válida'

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python license_verifier.py <ruta_license.lic>")
        exit(1)
    status, reason = verify_license(sys.argv[1])
    print(f"Estado: {status}\nMotivo: {reason}")
