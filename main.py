import uvicorn
from app.audio_upload import app

if __name__ == "__main__":
    print("App de transcripción iniciada.")
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False, log_level="debug"
)