
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

# Definir router ANTES de cualquier decorador
router = APIRouter(prefix="/transcript", tags=["transcript"])
AUDIO_DIR = Path(__file__).parent.parent / "audio"
TRANSCRIPTS_DIR = Path(__file__).parent.parent / "transcripts"
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
TRANSCRIPTS_DIR = Path(__file__).parent.parent / "transcripts"
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

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
@router.get("/list")
def list_transcripts():
    files = [f.name for f in TRANSCRIPTS_DIR.glob("*.txt")]
    return {"transcripts": files}
