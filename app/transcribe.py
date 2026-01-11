from fastapi import APIRouter, HTTPException, Body, Query, Request
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
from fastapi import Response
from docx import Document
import whisper
import os
import sys
import subprocess
import json
import numpy as np

# Detectar el directorio base correcto
if getattr(sys, 'frozen', False):
    # Estamos corriendo desde el .exe
    BASE_DIR = Path(sys.executable).parent
else:
    # Estamos en desarrollo
    BASE_DIR = Path(__file__).parent.parent

# Definir router ANTES de cualquier decorador
router = APIRouter(prefix="/transcript", tags=["transcript"])
AUDIO_DIR = BASE_DIR / "audio"
TRANSCRIPTS_DIR = BASE_DIR / "transcripts"
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

# --- DOCX export ---
def transcript_to_docx(transcript_path: Path) -> bytes:
    """Genera un archivo DOCX a partir de un archivo de texto de transcripción."""
    doc = Document()
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            doc.add_paragraph(line.rstrip())
    from io import BytesIO
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()

@router.get("/export_docx/{filename}")
def export_transcript_docx(filename: str):
    # Permitir nombre con o sin .txt
    transcript_path = TRANSCRIPTS_DIR / filename
    if not transcript_path.exists():
        if not filename.endswith('.txt'):
            transcript_path_txt = TRANSCRIPTS_DIR / f"{filename}.txt"
            if transcript_path_txt.exists():
                transcript_path = transcript_path_txt
            else:
                raise HTTPException(status_code=404, detail="Transcripción no encontrada")
        else:
            raise HTTPException(status_code=404, detail="Transcripción no encontrada")
    docx_bytes = transcript_to_docx(transcript_path)
    docx_filename = transcript_path.stem + ".docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename={docx_filename}"
        }
    )

@router.post("")
def transcribe_on_demand(filename: str = Query(..., description="Nombre del archivo de audio")):
    audio_path = AUDIO_DIR / filename
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail=f"Archivo de audio '{filename}' no encontrado")
    transcript_file = transcribe_audio(filename)
    transcript_path = TRANSCRIPTS_DIR / transcript_file
    if transcript_path.exists():
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_text = f.read()
    else:
        transcript_text = None
    return {"filename": transcript_file, "transcript": transcript_text, "message": "Transcripción generada correctamente"}

@router.get("/list")
def list_transcripts():
    files = [f.name for f in TRANSCRIPTS_DIR.glob("*.txt")]
    return {"transcripts": files}

# Forzar ruta de ffmpeg para Whisper y subprocess
FFMPEG_DIR = str(BASE_DIR / "ffmpeg")
FFMPEG_PATH = str(BASE_DIR / "ffmpeg" / "ffmpeg.exe")

# Agregar la carpeta ffmpeg al PATH (no solo el ejecutable)
if os.path.exists(FFMPEG_PATH):
    os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

# Monkey-patch para que whisper use nuestro ffmpeg
import whisper.audio
original_load_audio = whisper.audio.load_audio

def custom_load_audio(file: str, sr: int = 16000):
    cmd = [
        FFMPEG_PATH,
        "-nostdin",
        "-threads", "0",
        "-i", file,
        "-f", "s16le",
        "-ac", "1",
        "-acodec", "pcm_s16le",
        "-ar", str(sr),
        "-"
    ]
    
    try:
        out = subprocess.run(cmd, capture_output=True, check=True).stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e
    
    return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0

# Reemplazar la función original
whisper.audio.load_audio = custom_load_audio

model = whisper.load_model("base")  # Puedes cambiar a "small", "medium", etc.

# Función para transcribir audio y guardar resultado
def transcribe_audio(filename: str):
    audio_path = AUDIO_DIR / filename
    if not audio_path.exists():
        raise FileNotFoundError(f"Archivo de audio '{filename}' no encontrado")
    result = model.transcribe(str(audio_path), verbose=True, language="es")
    segments = result.get("segments", [])
    paragraphs = {}
    for seg in segments:
        minute = int(seg['start'] // 60)
        if minute not in paragraphs:
            paragraphs[minute] = []
        paragraphs[minute].append(f"[{seg['start']:.2f}-{seg['end']:.2f}] {seg['text']}")
    base_name = audio_path.stem
    transcript_path = TRANSCRIPTS_DIR / f"{base_name}.txt"
    with open(transcript_path, "w", encoding="utf-8") as f:
        for minute, texts in paragraphs.items():
            f.write(f"--- Minuto {minute} ---\n")
            f.write("\n".join(texts) + "\n\n")
    return transcript_path.name

@router.get("/{filename}")
def get_transcript(filename: str):
    # Buscar el archivo de transcripción asociado al audio, permitiendo nombre con o sin .txt
    transcript_path = TRANSCRIPTS_DIR / filename
    if not transcript_path.exists():
        # Si no existe, probar agregando .txt si no lo tiene
        if not filename.endswith('.txt'):
            transcript_path_txt = TRANSCRIPTS_DIR / f"{filename}.txt"
            if transcript_path_txt.exists():
                transcript_path = transcript_path_txt
            else:
                raise HTTPException(status_code=404, detail="Transcripción no encontrada")
        else:
            raise HTTPException(status_code=404, detail="Transcripción no encontrada")
    with open(transcript_path, "r", encoding="utf-8") as f:
        text = f.read()
    return {"filename": transcript_path.name, "text": text}

@router.get("/download/{filename}")
def download_transcript(filename: str):
    transcript_path = TRANSCRIPTS_DIR / filename
    if not transcript_path.exists():
        raise HTTPException(status_code=404, detail="Transcripción no encontrada")
    return FileResponse(transcript_path, media_type="text/plain", filename=filename)

@router.put("/{filename}")
def update_transcript(filename: str, text: str = Body(..., embed=True)):
    # Permitir nombre con o sin .txt
    transcript_path = TRANSCRIPTS_DIR / filename
    if not transcript_path.exists():
        # Si no existe, probar agregando .txt
        transcript_path_txt = TRANSCRIPTS_DIR / f"{filename}.txt"
        if transcript_path_txt.exists():
            transcript_path = transcript_path_txt
        else:
            raise HTTPException(status_code=404, detail="Transcripción no encontrada")
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(text)
    return {"filename": transcript_path.name, "message": "Transcripción actualizada"}

@router.delete("/{filename}")
def delete_transcript(filename: str):
    # Permitir nombre con o sin .txt
    transcript_path = TRANSCRIPTS_DIR / filename
    if not transcript_path.exists():
        transcript_path_txt = TRANSCRIPTS_DIR / f"{filename}.txt"
        if transcript_path_txt.exists():
            transcript_path = transcript_path_txt
        else:
            raise HTTPException(status_code=404, detail="Transcripción no encontrada")
    transcript_path.unlink()
    return {"filename": transcript_path.name, "message": "Transcripción eliminada"}