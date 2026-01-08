# App de Transcripción Local

## Archivos excluidos del repositorio
Este proyecto incluye un archivo `.gitignore` que excluye:
- `audio/` y `transcripts/` (no se suben archivos de usuario ni transcripciones generadas)
- `ffmpeg.exe` (debe descargarse manualmente)
- `__pycache__/` y archivos `.pyc`
- `.env` (si usas variables de entorno)


## Requisitos
- Python 3.10+ y FastAPI
- Instalar dependencias con `pip install -r requirements.txt`
- Descargar ffmpeg.exe y colocarlo en la raíz del proyecto (`LxT-Back/ffmpeg.exe`). Es obligatorio para la transcripción.
- Modelos Whisper instalados (por defecto se usa el modelo 'base')
- Solo se soporta idioma español
- Formatos de audio recomendados: mp3, wav, m4a

**Importante:** ffmpeg.exe no se incluye en el repositorio por temas de licencia y tamaño. Descárgalo desde https://ffmpeg.org/download.html y colócalo en la carpeta principal.

## Funcionalidades
- Subida de archivos de audio
- Transcripción automática: al subir un audio, se genera el transcript automáticamente y queda disponible en la carpeta `transcripts/`.
- Edición manual de transcripciones
- Exportación y descarga de transcripciones en .txt
- Listado de audios y transcripciones disponibles

## Uso
1. Instala dependencias con `pip install -r requirements.txt`
2. Descarga y coloca ffmpeg.exe en la raíz del proyecto.
3. Inicia el backend con `python main.py`
4. Accede a la documentación interactiva en [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
5. Sube un archivo de audio y la transcripción se genera automáticamente.
6. Consulta, edita y descarga la transcripción.

## Notas
- Si el archivo de audio es muy grande, puede tardar en procesarse.
- Si el formato no es soportado, el sistema mostrará un error.
- Todas las transcripciones se generan en español.
- Si ffmpeg.exe no está en la raíz, la transcripción fallará y el backend mostrará un error.

## Errores comunes
- **Archivo no soportado:** Verifica el formato y la calidad del audio.
- **ffmpeg no encontrado:** Descarga ffmpeg.exe y colócalo en la raíz del proyecto.
- **Transcripción vacía:** Puede ocurrir si el audio está vacío o no tiene voz clara.
- **404 al consultar transcript:** Asegúrate de usar el nombre base del audio (por ejemplo, Recording.txt) y que la transcripción se haya generado correctamente.

---
Desarrollado con FastAPI y Whisper para uso local y privado.
