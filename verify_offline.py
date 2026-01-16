"""
Script de verificación para asegurar que todo está listo para funcionamiento OFFLINE.
"""
import os
from pathlib import Path

print("=" * 70)
print("VERIFICACIÓN DE CONFIGURACIÓN OFFLINE")
print("=" * 70)

# ====== 1. VERIFICAR MODELOS DE WHISPER ======
print("\n[1/5] Verificando modelos de Whisper...")
whisper_cache = Path.home() / ".cache" / "whisper"
whisper_models = ["tiny.pt", "base.pt", "small.pt", "medium.pt", "large-v2.pt", "large-v3.pt"]

if whisper_cache.exists():
    print(f"  ✓ Directorio de caché encontrado: {whisper_cache}")
    found_models = list(whisper_cache.glob("*.pt"))
    print(f"  → Modelos encontrados: {len(found_models)}")
    for model in found_models:
        print(f"    • {model.name} ({model.stat().st_size / (1024**3):.2f} GB)")
    
    required_models = ["tiny.pt", "base.pt", "small.pt", "medium.pt"]
    missing = [m for m in required_models if not (whisper_cache / m).exists()]
    if missing:
        print(f"  ⚠ Modelos faltantes: {missing}")
        print(f"  → Ejecuta: python download_models.py")
    else:
        print(f"  ✓ Todos los modelos principales están descargados")
else:
    print(f"  ✗ ERROR: No se encontró el directorio de caché")
    print(f"  → Ejecuta: python download_models.py")

# ====== 2. VERIFICAR MODELO DE PYANNOTE ======
print("\n[2/5] Verificando modelo de Pyannote (diarización)...")
hf_cache = Path.home() / ".cache" / "huggingface"

if hf_cache.exists():
    print(f"  ✓ Directorio de HuggingFace encontrado: {hf_cache}")
    
    # Buscar modelos de pyannote (buscar en subdirectorios)
    pyannote_dirs = list(hf_cache.rglob("*pyannote*"))
    if pyannote_dirs:
        print(f"  ✓ Encontrados {len(pyannote_dirs)} archivos/directorios de Pyannote")
        
        # Verificar modelo específico
        speaker_diarization = list(hf_cache.rglob("*speaker-diarization-3.1*"))
        if speaker_diarization:
            print(f"  ✓ Modelo de diarización 3.1 encontrado")
        else:
            print(f"  ⚠ Modelo de diarización 3.1 NO encontrado")
            print(f"  → Ejecuta: python download_models.py")
    else:
        print(f"  ✗ No se encontraron modelos de Pyannote")
        print(f"  → Ejecuta: python download_models.py")
else:
    print(f"  ✗ ERROR: No se encontró el directorio de HuggingFace")
    print(f"  → Ejecuta: python download_models.py")

# ====== 3. VERIFICAR FFMPEG ======
print("\n[3/5] Verificando FFmpeg...")
ffmpeg_exe = Path("ffmpeg.exe")
ffprobe_exe = Path("ffprobe.exe")

if ffmpeg_exe.exists():
    size_mb = ffmpeg_exe.stat().st_size / (1024**2)
    print(f"  ✓ ffmpeg.exe encontrado ({size_mb:.1f} MB)")
else:
    print(f"  ✗ ERROR: ffmpeg.exe NO encontrado")
    print(f"  → Descarga desde: https://ffmpeg.org/download.html")

if ffprobe_exe.exists():
    size_mb = ffprobe_exe.stat().st_size / (1024**2)
    print(f"  ✓ ffprobe.exe encontrado ({size_mb:.1f} MB)")
else:
    print(f"  ✗ ERROR: ffprobe.exe NO encontrado")
    print(f"  → Descarga desde: https://ffmpeg.org/download.html")

# ====== 4. VERIFICAR .ENV ======
print("\n[4/5] Verificando configuración (.env)...")
env_file = Path(".env")

if env_file.exists():
    print(f"  ✓ Archivo .env encontrado")
    
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    if "HF_TOKEN" in env_content:
        print(f"  ✓ HF_TOKEN configurado")
    else:
        print(f"  ⚠ HF_TOKEN NO configurado (diarización deshabilitada)")
    
    if "WHISPER_MODEL" in env_content:
        print(f"  ✓ WHISPER_MODEL configurado")
else:
    print(f"  ✗ ERROR: Archivo .env NO encontrado")
    print(f"  → Crea un archivo .env con HF_TOKEN")

# ====== 5. VERIFICAR PyInstaller SPEC ======
print("\n[5/5] Verificando configuración de build...")
spec_file = Path("transcription-backend.spec")

if spec_file.exists():
    print(f"  ✓ Archivo .spec encontrado")
    
    with open(spec_file, 'r', encoding='utf-8') as f:
        spec_content = f.read()
    
    checks = {
        "whisper_cache": "whisper_cache" in spec_content,
        "huggingface_cache": "huggingface_cache" in spec_content,
        "ffmpeg_binaries": "ffmpeg_binaries" in spec_content or "ffmpeg.exe" in spec_content,
        "pyannote_datas": "pyannote_datas" in spec_content or "pyannote" in spec_content,
    }
    
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}: {'incluido' if passed else 'FALTANTE'}")
    
    if all(checks.values()):
        print(f"  ✓ Configuración completa para build offline")
    else:
        print(f"  ⚠ Revisar configuración del .spec")
else:
    print(f"  ✗ ERROR: Archivo .spec NO encontrado")

# ====== RESUMEN FINAL ======
print("\n" + "=" * 70)
print("RESUMEN")
print("=" * 70)

print("\n📋 Checklist para funcionamiento OFFLINE:")
print("  [ ] Modelos de Whisper descargados (tiny, base, small, medium, large)")
print("  [ ] Modelo de Pyannote descargado (speaker-diarization-3.1)")
print("  [ ] FFmpeg y FFprobe en directorio raíz")
print("  [ ] Archivo .env con HF_TOKEN configurado")
print("  [ ] Archivo .spec actualizado con todas las dependencias")

print("\n🚀 Próximos pasos:")
print("  1. Si faltan modelos: python download_models.py")
print("  2. Verificar que todo está ✓ arriba")
print("  3. Hacer build: pyinstaller transcription-backend.spec")
print("  4. Probar ejecutable sin conexión a internet")

print("\n💡 IMPORTANTE:")
print("  • Los modelos ocupan ~3-5 GB en total")
print("  • El build final será de ~1.5-2 GB")
print("  • Asegúrate de tener suficiente espacio en disco")
print()
