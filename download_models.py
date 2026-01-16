"""
Script para pre-descargar TODOS los modelos necesarios para funcionamiento offline.
Ejecutar ANTES de hacer el build con PyInstaller.
"""
import os
import whisper
from pyannote.audio import Pipeline
import torch
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("=" * 60)
print("DESCARGA DE MODELOS PARA FUNCIONAMIENTO OFFLINE")
print("=" * 60)

# ====== 1. DESCARGAR TODOS LOS MODELOS DE WHISPER ======
print("\n[1/2] Descargando modelos de Whisper...")
whisper_models = ["tiny", "base", "small", "medium", "large"]

for model_name in whisper_models:
    try:
        print(f"\n  -> Descargando modelo '{model_name}'...")
        model = whisper.load_model(model_name)
        print(f"  [OK] Modelo '{model_name}' descargado correctamente")
        
        # Liberar memoria
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception as e:
        print(f"  [ERROR] Error descargando '{model_name}': {e}")

print("\n[OK] Todos los modelos de Whisper descargados")
print(f"  Ubicación: {os.path.expanduser('~/.cache/whisper')}")

# ====== 2. DESCARGAR MODELO DE PYANNOTE ======
print("\n[2/2] Descargando modelo de diarización (Pyannote)...")

hf_token = os.getenv("HF_TOKEN")
if not hf_token:
    print("  [ERROR] HF_TOKEN no configurado en .env")
    print("  -> Agrega tu token de Hugging Face en el archivo .env")
    print("  -> Obten tu token en: https://huggingface.co/settings/tokens")
else:
    try:
        print(f"  -> Descargando 'pyannote/speaker-diarization-3.1'...")
        # Intentar con 'token' primero (versión nueva), luego 'use_auth_token' (versión antigua)
        try:
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=hf_token
            )
        except TypeError:
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token
            )
        print(f"  [OK] Modelo de diarizacion descargado correctamente")
        print(f"  Ubicacion: {os.path.expanduser('~/.cache/huggingface')}")
        
        # Liberar memoria
        del pipeline
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception as e:
        print(f"  [ERROR] Error descargando modelo de diarizacion: {e}")

# ====== RESUMEN FINAL ======
print("\n" + "=" * 60)
print("RESUMEN")
print("=" * 60)
print("\nModelos descargados en:")
print(f"  • Whisper: {os.path.expanduser('~/.cache/whisper')}")
print(f"  • Pyannote: {os.path.expanduser('~/.cache/huggingface')}")
print("\nProximos pasos:")
print("  1. Verificar que los modelos se descargaron correctamente")
print("  2. Ejecutar PyInstaller: pyinstaller transcription-backend.spec")
print("  3. Los modelos se incluiran automaticamente en el build")
print("\n[OK] Listo para build offline!\n")
