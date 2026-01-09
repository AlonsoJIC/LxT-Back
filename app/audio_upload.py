
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.transcribe import router as transcribe_router
from fastapi.middleware.cors import CORSMiddleware
import datetime
import subprocess

app = FastAPI()

from fastapi import FastAPI, File, UploadFile
app = FastAPI()
from fastapi.responses import JSONResponse
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import datetime
import subprocess


# Audio router
audio_router = APIRouter(prefix="/audio", tags=["audio"])
AUDIO_DIR = Path(__file__).parent.parent / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_audio_duration(file_path):
    try:
        cmd = [
            str(Path(__file__).parent.parent / "ffprobe.exe"),
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout.strip()
        duration = float(output) if output else None
        return round(duration, 1) if duration is not None else None
    except Exception as e:
        print(f"Error obteniendo duración de {file_path}: {e}")
        return None

@audio_router.get("/list")
def list_audios():
    files = []
    for f in AUDIO_DIR.glob("*"):
        if f.is_file():
            created_at = datetime.datetime.fromtimestamp(f.stat().st_ctime).strftime("%Y-%m-%d %H:%M")
            duration = get_audio_duration(f)
            files.append({
                "id": str(f),
                "filename": f.name,
                "created_at": created_at,
                "duration": duration
            })
    return {"audios": files}

@audio_router.post("/upload")
def upload_audio(file: UploadFile = File(...)):
    allowed_ext = {'.mp3', '.wav', '.m4a', '.webm', '.ogg', '.aac', '.flac', '.amr'}
    ext = Path(file.filename).suffix.lower()
    # Validar que el archivo sea de tipo audio/*
    if not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=415, detail=f"Tipo MIME no soportado: {file.content_type}. Debe ser audio/*.")
    if ext not in allowed_ext:
        # Permitir extensiones desconocidas pero advertir
        pass  # Opcional: puedes registrar un warning aquí
    file_location = AUDIO_DIR / file.filename
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    from app.transcribe import transcribe_audio
    try:
        transcript_file = transcribe_audio(file.filename)
        transcript_path = Path(__file__).parent.parent / "transcripts" / transcript_file
        if transcript_path.exists():
            with open(transcript_path, "r", encoding="utf-8") as f:
                transcript_text = f.read()
        else:
            transcript_text = None
    except Exception as e:
        transcript_text = None
        return JSONResponse(content={"filename": file.filename, "message": f"Archivo subido pero error en transcripción: {e}"}, status_code=500)
    return JSONResponse(content={"filename": file.filename, "message": "Archivo subido y transcrito correctamente", "transcript": transcript_text})
@audio_router.delete("/{filename}")
def delete_audio(filename: str):
    allowed_ext = ['.mp3', '.wav', '.m4a']
    base = Path(filename).stem
    ext = Path(filename).suffix.lower()
    candidates = []
    if ext in allowed_ext:
        candidates.append(AUDIO_DIR / filename)
    else:
        for e in allowed_ext:
            candidates.append(AUDIO_DIR / f"{base}{e}")
    found = None
    for c in candidates:
        if c.exists():
            found = c
            break
    transcript_path = Path(__file__).parent.parent / "transcripts" / f"{base}.mp3.txt"
    deleted = False
    if found:
        found.unlink()
        deleted = True
    if transcript_path.exists():
        transcript_path.unlink()
    if deleted:
        return {"message": f"Audio y transcripción '{found.name}' eliminados"}
    else:
        available = [f.name for f in AUDIO_DIR.glob('*') if f.is_file()]
        raise HTTPException(status_code=404, detail=f"Audio '{filename}' no encontrado. Audios disponibles: {available}")

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    transcribe_audio(file.filename)
    return JSONResponse(content={"filename": file.filename, "message": "Archivo subido y transcrito correctamente"})



# Registrar routers al final del archivo
app.include_router(audio_router)
app.include_router(transcribe_router)


