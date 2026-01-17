"""
fingerprint.py
Genera un identificador único de máquina (machine_id) combinando datos de hardware y sistema operativo.
No expone datos crudos, solo el hash SHA-256 final.
"""
import hashlib
import platform
import uuid
import os
import re


def get_mac_address() -> str:
    # Obtiene la MAC address principal (sin separadores)
    mac = uuid.getnode()
    return f"{mac:012x}"


def get_disk_serial() -> str:
    # Obtiene el serial del primer disco fijo (Windows moderno)
    if os.name == "nt":
        try:
            import subprocess
            # Usar PowerShell para mayor compatibilidad
            ps_cmd = (
                "Get-WmiObject Win32_DiskDrive | Where-Object { $_.MediaType -eq 'Fixed hard disk media' } | "
                "Select-Object -First 1 -ExpandProperty SerialNumber"
            )
            output = subprocess.check_output([
                "powershell", "-Command", ps_cmd
            ], encoding="utf-8", errors="ignore")
            serial = output.strip().replace(" ", "")
            if serial and len(serial) > 0:
                return serial[:32]  # Limitar longitud
        except Exception:
            pass
        # Fallback: intentar con wmic si PowerShell falla
        try:
            output = subprocess.check_output(
                "wmic diskdrive where MediaType='Fixed hard disk media' get SerialNumber /value", shell=True, encoding="utf-8", errors="ignore"
            )
            match = re.search(r"SerialNumber=([A-Za-z0-9]+)", output)
            if match:
                return match.group(1)[:32]
        except Exception:
            pass
        return "unknown_win"
    # Otros sistemas: no implementado
    return "unknown_os"


def get_cpu_info() -> str:
    # Obtiene información básica de CPU
    return platform.processor() or "unknown"


def get_os_info() -> str:
    # Obtiene información del sistema operativo
    return f"{platform.system()} {platform.release()}"


def normalize_data(*args) -> str:
    # Normaliza y concatena los datos con '|'
    norm = [str(a).strip().lower().replace(" ", "") for a in args]
    return "|".join(norm)


def generate_machine_id() -> str:
    mac = get_mac_address()
    disk = get_disk_serial()
    cpu = get_cpu_info()
    osinfo = get_os_info()
    data = normalize_data(mac, disk, cpu, osinfo)
    hash_bytes = hashlib.sha256(data.encode("utf-8")).hexdigest()
    return hash_bytes.upper()

if __name__ == "__main__":
    print("Machine ID:", generate_machine_id())
