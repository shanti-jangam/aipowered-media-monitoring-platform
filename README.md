# SmartMedia Analyst: Real-Time AI-Powered Media Monitoring & Control Platform

A microservices-based platform that ingests live media streams (YouTube, radio, podcasts) and uses advanced AI to transcribe, analyze, and control content in real-time. Built with FastAPI, Docker, PostgreSQL, and Hugging Face Transformers.

## Project Overview

**SmartMedia Analyst** solves real-world problems for:
- **Media companies**: Monitor and react to live content
- **Brands**: Track mentions and sentiment
- **Regulators**: Flag policy violations
- **Enterprises**: Automate compliance and crisis response

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Media Sources  │───▶│ Media Ingestion │───▶│  AI Processing  │
│ (YouTube, etc.) │    │   (FastAPI)     │    │   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌─────────────────┐    ┌─────────────────┐
         └─────────────▶│   PostgreSQL    │    │   MCP Server    │
                        │   (Database)    │    │  (Media Control)│
                        └─────────────────┘    └─────────────────┘
```

### Microservices

1. **Media Ingestion Service** (`:81 - Accepts YouTube/stream URLs
   - Downloads and chunks audio using `yt-dlp` and `ffmpeg`
   - Sends chunks to AI Processing service
   - Stores transcripts in PostgreSQL

2Processing Service** (`:8002  - Speech-to-text using Hugging Face (`openai/whisper-tiny`)
   - Real-time audio transcription
   - Returns structured transcript data
3 **MCP Server** (`:8003
   - Remote media stream control (pause, resume, record, switch)
   - AI-triggered actions (auto-pause on hate speech, auto-record on breaking news)
   - Stream status monitoring and recording history

4. **PostgreSQL Database** (`:5432Stores transcripts and metadata
   - Persistent data for analysis and compliance

## Quick Start

### Prerequisites
- Docker Desktop
- Python 3.10+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd aiml_project
   ```

2. **Start all services**
   ```bash
   docker-compose up --build
   ```

3. **Initialize the database** (first time only)
   ```bash
   docker-compose run --rm media_ingestion python init_db.py
   ```

4. **Verify services are running**
   - Media Ingestion: http://localhost:8001
   - AI Processing: http://localhost:8002- MCP Server: http://localhost:8003 PostgreSQL: localhost:5432

## API Documentation

### Media Ingestion Service

**Ingest a YouTube URL:**
```bash
curl -X POST http://localhost:801t/ \
  -H "Content-Type: application/json" \
  -d {"url": "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"}'
```

### AI Processing Service

**Transcribe an audio chunk:**
```bash
curl -X POST http://localhost:8002/asr/ \
  -F "file=@path/to/audio_chunk.wav"
```

### MCP Server

**Control a media stream:**
```bash
# Pause a stream
curl -X POST http://localhost:803/mcp/control \
  -H "Content-Type: application/json undefined
  -d '{stream_id:your-stream-id", action": "pause"}'

# Resume a stream
curl -X POST http://localhost:803/mcp/control \
  -H "Content-Type: application/json undefined
  -d '{stream_id:your-stream-id",action": "resume"}'

# Start recording
curl -X POST http://localhost:803/mcp/control \
  -H "Content-Type: application/json undefined
  -d '{stream_id:your-stream-id",action": "record}'

# Switch to a different URL
curl -X POST http://localhost:803/mcp/control \
  -H "Content-Type: application/json undefined
  -d '{stream_id:your-stream-id",action":switch, arget_url": "https://youtube.com/watch?v=NEW_VIDEO}'
```

**AI-triggered actions:**
```bash
# Auto-pause on hate speech detection
curl -X POST http://localhost:83/mcp/ai-trigger \
  -H "Content-Type: application/json" \
  -d[object Object]    stream_id:your-stream-id",
    trigger_type:hate_speech,
    confidence": 0.85transcript_segment": "detected hate speech content"
  }'

# Auto-record on breaking news
curl -X POST http://localhost:83/mcp/ai-trigger \
  -H "Content-Type: application/json" \
  -d[object Object]    stream_id:your-stream-id",
   trigger_type":breaking_news,
    confidence": 0.92transcript_segment": "breaking news content"
  }'
```

**Get stream status:**
```bash
curl http://localhost:803status/your-stream-id
```

**List all active streams:**
```bash
curl http://localhost:8003/mcp/streams
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=smartmedia

# AI Processing
AI_PROCESSING_URL=http://ai_processing:8000/asr/

# Media Ingestion
CHUNKS_DIR=./services/media_ingestion/chunks
```

### Hugging Face Model Cache

The project uses a pre-downloaded Hugging Face model cache to avoid download timeouts. The cache is mounted from your host to the Docker container.

## Database Schema

### Transcripts Table
```sql
CREATE TABLE transcripts (
    id SERIAL PRIMARY KEY,
    stream_id VARCHAR(128),
    chunk_filename VARCHAR(256   transcript TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Testing

### Test the Full Pipeline

1. **Ingest a YouTube video:**
   ```bash
   curl -X POST http://localhost:801/ingest/ \
     -H "Content-Type: application/json\
     -d {"url": "https://www.youtube.com/watch?v=vP4iY1TtS3s"}'
   ```

2. **Check for chunk files:**
   ```bash
   ls services/media_ingestion/chunks/
   ```

3. **Test transcription:**
   ```bash
   curl -X POST http://localhost:802r/ \
     -F "file=@services/media_ingestion/chunks/YOUR_CHUNK_FILE.wav"
   ```

4. **Check database contents:**
   ```bash
   docker-compose exec db psql -U postgres -d smartmedia -c "SELECT * FROM transcripts LIMIT 5;   ```

### Test MCP Server

1eate a test stream:**
   ```bash
   curl -X POST http://localhost:83mcp/control \
     -H "Content-Type: application/json" \
     -d '{stream_id": "test-stream", action": pause"}'
   ```
2heck stream status:**
   ```bash
   curl http://localhost:803status/test-stream
   ```

## Deployment

### Production Considerations1 **Database**: Use managed PostgreSQL (AWS RDS, Google Cloud SQL, etc.)
2. **Caching**: Add Redis for real-time events and caching
3*Monitoring**: Add logging and monitoring (ELK stack, Prometheus)
4. **Security**: Implement authentication and authorization
5. **Scaling**: Use Kubernetes for container orchestration

### Docker Compose for Production

```yaml
version:3.8
services:
  media_ingestion:
    build: ./services/media_ingestion
    ports:
      - "8001:8000
    environment:
      - DATABASE_URL=postgresql://user:pass@host:5432/db
    depends_on:
      - db

  ai_processing:
    build: ./services/ai_processing
    ports:
      - "8002:8000
    environment:
      - MODEL_CACHE_PATH=/app/models
    volumes:
      - model_cache:/app/models

  mcp_server:
    build: ./services/mcp_server
    ports:
      -8003

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
  model_cache:
```

## Acknowledgments

- [Hugging Face](https://huggingface.co/) for the ASR models
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Docker](https://www.docker.com/) for containerization
- [PostgreSQL](https://www.postgresql.org/) for the database
