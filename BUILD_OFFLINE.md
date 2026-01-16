# 🎯 Guía de Build Offline - Backend de Transcripción

## 📦 Requisitos Previos

- Python 3.9 o superior
- Token de HuggingFace (para diarización)
- ~5 GB de espacio libre en disco
- Conexión a internet (solo para la descarga inicial)

---

## 🔧 Configuración Inicial

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### 2. Configurar Token de HuggingFace

Crea un archivo `.env` en la raíz del proyecto:

```env
HF_TOKEN=tu_token_aqui
WHISPER_MODEL=small
```

**¿Cómo obtener el token?**
1. Ve a https://huggingface.co/settings/tokens
2. Crea un token de lectura (Read)
3. Copia y pega en `.env`

### 3. Descargar FFmpeg

Si no tienes `ffmpeg.exe` y `ffprobe.exe` en la raíz:

1. Descarga desde: https://ffmpeg.org/download.html
2. Extrae `ffmpeg.exe` y `ffprobe.exe` a la raíz del proyecto

---

## 📥 Descargar Modelos (CRÍTICO para Offline)

### Paso 1: Ejecutar Script de Descarga

```bash
python download_models.py
```

Este script descargará:
- ✅ 5 modelos de Whisper (tiny, base, small, medium, large)
- ✅ Modelo de diarización de Pyannote

**Ubicación de los modelos:**
- Whisper: `~/.cache/whisper/` (~3 GB)
- Pyannote: `~/.cache/huggingface/` (~1.5 GB)

### Paso 2: Verificar Descarga

```bash
python verify_offline.py
```

Deberías ver ✓ en todos los checks. Si algo falta, vuelve a ejecutar `download_models.py`.

---

## 🏗️ Crear Build Offline

### 1. Ejecutar PyInstaller

```bash
pyinstaller transcription-backend.spec
```

Este comando:
1. Empaqueta el código Python
2. Incluye los modelos descargados
3. Incluye FFmpeg
4. Crea un ejecutable standalone

### 2. Ubicación del Build

```
dist/
└── transcription-backend.exe   # Ejecutable principal
└── whisper_models/              # Modelos de Whisper
└── huggingface/                 # Modelo de Pyannote
└── audio/                       # Carpeta de audios
└── transcripts/                 # Carpeta de transcripciones
└── .env                         # Configuración
└── ffmpeg.exe
└── ffprobe.exe
```

---

## ✅ Verificación del Build

### 1. Probar sin Internet

1. **Desconecta internet** (importante)
2. Ve a `dist/`
3. Ejecuta `transcription-backend.exe`
4. Deberías ver: `App de transcripción iniciada.`

### 2. Probar Endpoints

Abre otro terminal y prueba:

```bash
# Ver modelos disponibles
curl http://localhost:8000/

# Subir audio
curl -X POST http://localhost:8000/audio/upload -F "file=@test.mp3"

# Encolar transcripción
curl -X POST "http://localhost:8000/transcript/queue?filename=test.mp3&model=small"

# Consultar estado
curl http://localhost:8000/transcript/status/TASK_ID_AQUI
```

Si todo funciona **sin internet**, ¡el build está correcto! ✅

---

## 📊 Modelos Disponibles

| Modelo | Tamaño | RAM Requerida | Velocidad | Calidad |
|--------|--------|---------------|-----------|---------|
| tiny   | 39 MB  | ~1 GB         | Muy rápida| Baja    |
| base   | 140 MB | ~1 GB         | Rápida    | Media   |
| small  | 244 MB | ~2 GB         | Media     | Buena   |
| medium | 769 MB | ~5 GB         | Lenta     | Muy buena|
| large  | 1.5 GB | ~10 GB        | Muy lenta | Excelente|

**Recomendación para PCs de bajo rendimiento:**
- Usar `small` como predeterminado
- Ofrecer `tiny` para velocidad máxima
- `medium` solo si tienen 8+ GB RAM

---

## 🐛 Solución de Problemas

### Error: "Modelo no encontrado"

**Causa:** Los modelos no se empaquetaron correctamente.

**Solución:**
```bash
# 1. Verificar que los modelos se descargaron
python verify_offline.py

# 2. Limpiar builds anteriores
rm -rf build/ dist/

# 3. Volver a hacer build
pyinstaller --clean transcription-backend.spec
```

### Error: "HF_TOKEN no configurado"

**Causa:** El archivo `.env` no se incluyó en el build.

**Solución:**
1. Verifica que `.env` existe en la raíz
2. Verifica que `transcription-backend.spec` incluye:
   ```python
   ('.env', '.'),
   ```

### Error: "FFmpeg no encontrado"

**Causa:** FFmpeg no se empaquetó.

**Solución:**
1. Verifica que `ffmpeg.exe` y `ffprobe.exe` están en la raíz
2. Verifica en `.spec`:
   ```python
   ffmpeg_binaries = [
       ('ffmpeg.exe', '.'),
       ('ffprobe.exe', '.'),
   ]
   ```

### Build muy lento

Es normal. El build puede tardar 5-15 minutos dependiendo de:
- Velocidad del disco
- CPU
- Cantidad de modelos

---

## 📝 Checklist Final

Antes de distribuir el build:

- [ ] ✅ Todos los modelos descargados (`verify_offline.py`)
- [ ] ✅ Build completado sin errores
- [ ] ✅ Ejecutable funciona **sin internet**
- [ ] ✅ Transcripciones funcionan con los 5 modelos
- [ ] ✅ Diarización funciona (identifica hablantes)
- [ ] ✅ Archivo `.env` incluido (sin token expuesto públicamente)
- [ ] ✅ FFmpeg funciona (no hay errores de audio)

---

## 🚀 Distribución

El build final (`dist/transcription-backend.exe`) es **portable**:

- ✅ No requiere instalación
- ✅ No requiere Python instalado
- ✅ No requiere internet
- ✅ Incluye todos los modelos
- ✅ Funciona en cualquier Windows (mismo CPU architecture)

**Tamaño aproximado del build:** 1.5-2.5 GB

---

## 🔒 Seguridad

⚠️ **IMPORTANTE:** 

- NO distribuyas el build con tu `HF_TOKEN` personal
- Genera un token de solo lectura para distribución
- O pide a cada usuario que configure su propio token

---

## 📞 Soporte

Si algo no funciona:

1. Ejecuta `verify_offline.py` y revisa los errores
2. Revisa los logs en la consola del ejecutable
3. Verifica que no hay antivirus bloqueando

---

**Última actualización:** Enero 2026
