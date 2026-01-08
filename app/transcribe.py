
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import whisper
import os
import sys

import subprocess
import json

router = APIRouter(prefix="/transcript", tags=["transcript"])
AUDIO_DIR = Path(__file__).parent.parent / "audio"
TRANSCRIPTS_DIR = Path(__file__).parent.parent / "transcripts"
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

# Forzar ruta de ffmpeg para Whisper y subprocess
FFMPEG_PATH = str(Path(__file__).parent.parent / "ffmpeg" / "ffmpeg.exe")
if os.path.exists(FFMPEG_PATH):
    os.environ["PATH"] = FFMPEG_PATH + os.pathsep + os.environ.get("PATH", "")
    os.environ["FFMPEG_BINARY"] = FFMPEG_PATH

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

@router.get("/list")
def list_transcripts():
    files = [f.name for f in TRANSCRIPTS_DIR.glob("*.txt")]
    return {"transcripts": files}

@router.get("/{filename}")
def get_transcript(filename: str):
    # Buscar el archivo de transcripción asociado al audio
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
    audio_path = AUDIO_DIR / filename
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Archivo de audio no encontrado")
    result = model.transcribe(str(audio_path), verbose=True, language="es")
    segments = result.get("segments", [])
    paragraphs = {}
    for seg in segments:
        minute = int(seg['start'] // 60)
        if minute not in paragraphs:
            paragraphs[minute] = []
        paragraphs[minute].append(f"[{seg['start']:.2f}-{seg['end']:.2f}] {seg['text']}")
    # Guardar como {filename}.txt
    transcript_path = TRANSCRIPTS_DIR / f"{filename}.txt"
    with open(transcript_path, "w", encoding="utf-8") as f:
        for minute, texts in paragraphs.items():
            f.write(f"--- Minuto {minute} ---\n")
            f.write("\n".join(texts) + "\n\n")
    return JSONResponse(content={"transcript_file": transcript_path.name, "message": "Transcripción completada (español)"})

@router.get("/{filename}")
def get_transcript(filename: str):
    # Buscar el archivo de transcripción asociado al audio
    transcript_path = TRANSCRIPTS_DIR / f"{filename}.txt"
    if not transcript_path.exists():
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
@router.get("/list")
def list_transcripts():
    files = [f.name for f in TRANSCRIPTS_DIR.glob("*.txt")]
    return {"transcripts": files}
