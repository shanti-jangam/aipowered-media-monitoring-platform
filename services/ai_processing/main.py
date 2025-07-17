from fastapi import FastAPI, File, UploadFile, HTTPException
from transformers import pipeline
import tempfile
import shutil
import os

app = FastAPI()

# Global variable to store the ASR pipeline (loaded lazily)
asr_pipeline = None

def get_asr_pipeline():
    """Load ASR pipeline lazily when first needed"""
    global asr_pipeline
    if asr_pipeline is None:
        try:
            print("Loading ASR model...")
            # You can use 'openai/whisper-tiny' for fast, small model or 'facebook/wav2vec2-base-960h' for English
            asr_pipeline = pipeline(
                "automatic-speech-recognition", 
                model="openai/whisper-tiny",  # or "facebook/wav2vec2-base-960h"
                device=-1  # Use CPU
            )
            print("ASR model loaded successfully!")
        except Exception as e:
            print(f"Error loading ASR model: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to load ASR model: {str(e)}")
    return asr_pipeline

@app.post("/asr/")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        # Save uploaded file to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        
        # Get ASR pipeline (loads model if not already loaded)
        asr = get_asr_pipeline()
        
        # Run ASR
        result = asr(tmp_path)
        transcript = result["text"] if isinstance(result, dict) else result
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return {"transcript": transcript}
    except Exception as e:
        print(f"Error in transcription: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.get("/")
def read_root():
    return {"service": "ai_processing", "status": "running"}
