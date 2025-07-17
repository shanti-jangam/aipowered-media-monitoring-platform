from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import os
import subprocess
import uuid
import requests
import psycopg2

app = FastAPI()

CHUNKS_DIR = "chunks"
os.makedirs(CHUNKS_DIR, exist_ok=True)

AI_PROCESSING_URL = os.environ.get("AI_PROCESSING_URL", "http://ai_processing:8000/asr/")

class IngestRequest(BaseModel):
    url: str

def save_transcript_to_db(stream_id, chunk_filename, transcript):
    try:
        conn = psycopg2.connect(
            dbname="smartmedia",
            user="postgres",
            password="postgres",
            host="db",
            port=5432
        )
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO transcripts (stream_id, chunk_filename, transcript) VALUES (%s, %s, %s)""",
            (stream_id, chunk_filename, transcript)
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"Saved transcript for {chunk_filename} to DB.")
    except Exception as e:
        print(f"Error saving transcript to DB: {e}")

def send_chunk_for_transcription(chunk_path):
    with open(chunk_path, "rb") as f:
        files = {"file": (os.path.basename(chunk_path), f, "audio/wav")}
        try:
            resp = requests.post(AI_PROCESSING_URL, files=files, timeout=120)
            if resp.ok:
                transcript = resp.json().get("transcript", "")
                print(f"Transcript for {chunk_path}: {transcript}")
                # Extract session_id from chunk filename
                chunk_filename = os.path.basename(chunk_path)
                stream_id = chunk_filename.split("_")[0]  # session_id is before first _
                save_transcript_to_db(stream_id, chunk_filename, transcript)
            else:
                print(f"Failed to transcribe {chunk_path}: {resp.text}")
        except Exception as e:
            print(f"Error sending {chunk_path} for transcription: {e}")

def download_and_chunk_audio(url: str):
    session_id = str(uuid.uuid4())
    output_pattern = os.path.join(CHUNKS_DIR, f"{session_id}_%03d.wav")
    ytdlp_cmd = [
        "yt-dlp", "-f", "bestaudio", "-o", "-", url
    ]
    ffmpeg_cmd = [
        "ffmpeg", "-i", "pipe:0", "-f", "segment", "-segment_time", "10", "-ar", "16000", "-ac", "1",
        output_pattern
    ]
    print(f"Starting download and chunking for: {url}")
    try:
        with subprocess.Popen(ytdlp_cmd, stdout=subprocess.PIPE) as ytdlp_proc:
            with subprocess.Popen(ffmpeg_cmd, stdin=ytdlp_proc.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as ffmpeg_proc:
                ytdlp_proc.stdout.close()
                out, err = ffmpeg_proc.communicate()
                if ffmpeg_proc.returncode != 0:
                    print(f"ffmpeg error: {err.decode()}")
    except Exception as e:
        print(f"Error during download and chunking: {e}")
    chunk_files = [os.path.join(CHUNKS_DIR, f) for f in os.listdir(CHUNKS_DIR) if f.startswith(session_id)]
    print(f"Chunks created: {chunk_files}")
    for chunk_path in chunk_files:
        send_chunk_for_transcription(chunk_path)

@app.post("/ingest/")
def ingest_stream(req: IngestRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(download_and_chunk_audio, req.url)
    return {"status": "ingestion_started", "url": req.url}

@app.get("/")
def read_root():
    return {"service": "media_ingestion", "status": "running"}
