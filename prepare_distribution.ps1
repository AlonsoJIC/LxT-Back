# Script para preparar la distribucion offline de LxT-Back
# Copia los modelos desde el cache al directorio de distribucion

Write-Host "Preparando distribucion offline..." -ForegroundColor Cyan

# Directorio de distribucion
$DistDir = "dist\transcription-backend"
$ModelsDir = "$DistDir\models"

# Crear estructura de carpetas
Write-Host "Creando estructura de carpetas..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "$ModelsDir\whisper" | Out-Null
New-Item -ItemType Directory -Force -Path "$ModelsDir\huggingface" | Out-Null

# Copiar modelos de Whisper
Write-Host "Copiando modelos de Whisper..." -ForegroundColor Yellow
$WhisperCache = "$env:USERPROFILE\.cache\whisper"
if (Test-Path $WhisperCache) {
    Copy-Item -Path "$WhisperCache\*" -Destination "$ModelsDir\whisper\" -Recurse -Force
    Write-Host "   Modelos de Whisper copiados" -ForegroundColor Green
} else {
    Write-Host "   No se encontro cache de Whisper" -ForegroundColor Red
}

# Copiar modelos de Hugging Face (pyannote)
Write-Host "Copiando modelos de Hugging Face (pyannote)..." -ForegroundColor Yellow
$HFCache = "$env:USERPROFILE\.cache\huggingface"
if (Test-Path $HFCache) {
    Copy-Item -Path "$HFCache\*" -Destination "$ModelsDir\huggingface\" -Recurse -Force
    Write-Host "   Modelos de Hugging Face copiados" -ForegroundColor Green
} else {
    Write-Host "   No se encontro cache de Hugging Face" -ForegroundColor Red
}

# Copiar binarios de FFmpeg
Write-Host "Copiando binarios de FFmpeg..." -ForegroundColor Yellow
if (Test-Path "ffmpeg.exe") {
    Copy-Item -Path "ffmpeg.exe" -Destination "$DistDir\" -Force
    Copy-Item -Path "ffprobe.exe" -Destination "$DistDir\" -Force
    Write-Host "   FFmpeg copiado" -ForegroundColor Green
} else {
    Write-Host "   No se encontraron binarios de FFmpeg" -ForegroundColor Red
}

# Copiar .env si existe
if (Test-Path ".env") {
    Copy-Item -Path ".env" -Destination "$DistDir\" -Force
    Write-Host "   Archivo .env copiado" -ForegroundColor Green
}

Write-Host ""
Write-Host "Distribucion lista en: $DistDir" -ForegroundColor Green
Write-Host ""
Write-Host "Estructura de distribucion:" -ForegroundColor Cyan
Write-Host "   transcription-backend.exe"
Write-Host "   models\"
Write-Host "      whisper\"
Write-Host "      huggingface\"
Write-Host "   ffmpeg.exe"
Write-Host "   ffprobe.exe"
Write-Host "   .env"
Write-Host ""
Write-Host "NOTA: El archivo license.lic NO esta incluido." -ForegroundColor Yellow
Write-Host "Cada instalacion necesitara su propia licencia." -ForegroundColor Yellow
