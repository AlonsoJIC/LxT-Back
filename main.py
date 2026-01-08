# Punto de entrada principal para la app de transcripción

import uvicorn

if __name__ == "__main__":
    print("App de transcripción iniciada.")
    uvicorn.run("app.audio_upload:app", host="127.0.0.1", port=8000, reload=True)
