from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
from typing import Dict, Optional, List
import uuid
from datetime import datetime

app = FastAPI()

# In-memory storage for active streams and their states
# In production, this would be in a database
active_streams: Dict[str, Dict] = {}
ream_records: Dict[str, List[Dict]] = {}

class StreamControlRequest(BaseModel):
    stream_id: str
    action: str  # pause, resume, record, stop, switch
    target_url: Optional[str] = None  # for switch action

class AIActionRequest(BaseModel):
    stream_id: str
    trigger_type: str  # hate_speech, breaking_news, brand_mention, etc.
    confidence: float
    transcript_segment: str

class StreamStatus(BaseModel):
    stream_id: str
    status: str  # active, paused, recording, stopped
    current_url: str
    start_time: str
    last_action: str

@app.post("/mcp/control")
async def control_stream(request: StreamControlRequest):
    """Control media streams (pause, resume, record, stop, switch)"""
    try:
        if request.stream_id not in active_streams:
            # Initialize new stream
            active_streams[request.stream_id] = {
                "status": "active",
                "current_url": request.target_url or "unknown",
                "start_time": datetime.now().isoformat(),
                "last_action": request.action,
                "is_recording": False
            }
        
        stream = active_streams[request.stream_id]
        
        if request.action == "pause":
            stream["status"] = "paused"
            stream["last_action"] = "paused"
            print(f"Stream {request.stream_id} paused")
            
        elif request.action == "resume":
            stream["status"] = "active"
            stream["last_action"] = "resumed"
            print(f"Stream {request.stream_id} resumed")
            
        elif request.action == "record":
            stream["is_recording"] = True
            stream["last_action"] = "recording started"
            if request.stream_id not in stream_records:
                stream_records[request.stream_id] = []
            stream_records[request.stream_id].append({
                "action": "record_start",
                "timestamp": datetime.now().isoformat(),
                "url": stream["current_url"]
            })
            print(f"Recording started for stream {request.stream_id}")
            
        elif request.action == "stop":
            stream["status"] = "stopped"
            stream["is_recording"] = False
            stream["last_action"] = "stopped"
            print(f"Stream {request.stream_id} stopped")
            
        elif request.action == "switch":
            if request.target_url:
                stream["current_url"] = request.target_url
                stream["last_action"] = f"switched to {request.target_url}"
                print(f"Stream {request.stream_id} switched to {request.target_url}")
            else:
                raise HTTPException(status_code=400, detail="target_url required for switch action")
        
        return {
            "status": "success",
            "stream_id": request.stream_id,
            "action": request.action,
            "current_status": stream["status"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Control action failed: {str(e)}")

@app.post("/mcp/ai-trigger")
async def ai_triggered_action(request: AIActionRequest):
    """Handle AI-triggered actions (auto-pause on hate speech, record on breaking news, etc.)"""
    try:
        if request.stream_id not in active_streams:
            raise HTTPException(status_code=404, detail="Stream not found")
        
        stream = active_streams[request.stream_id]
        
        # Define AI trigger actions
        if request.trigger_type == "hate_speech" and request.confidence > 0.7:            # Auto-pause on high-confidence hate speech detection
            stream["status"] = "paused"
            stream["last_action"] = "auto-paused due to hate speech"
            action_taken = "auto-paused"
            
        elif request.trigger_type == "breaking_news" and request.confidence > 0.8:            # Auto-record on breaking news
            stream["is_recording"] = True
            stream["last_action"] = "auto-recording due to breaking news"
            if request.stream_id not in stream_records:
                stream_records[request.stream_id] = []
            stream_records[request.stream_id].append({
                "action": "auto_record_start",
                "trigger": "breaking_news",
                "confidence": request.confidence,
                "transcript_segment": request.transcript_segment,
                "timestamp": datetime.now().isoformat()
            })
            action_taken = "auto-recording"
            
        elif request.trigger_type == "brand_mention" and request.confidence > 0.6:
            # Log brand mention for monitoring
            stream["last_action"] = "brand mention detected"
            action_taken = "logged"
            
        else:
            action_taken = "monitored"
        return {
            "status": "success",
            "stream_id": request.stream_id,
            "trigger_type": request.trigger_type,
            "confidence": request.confidence,
            "action_taken": action_taken,
            "current_status": stream["status"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI trigger action failed: {str(e)}")

@app.get("/mcp/status/{stream_id}")
async def get_stream_status(stream_id: str):
    """Get current status of a specific stream"""
    if stream_id not in active_streams:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    stream = active_streams[stream_id]
    return StreamStatus(
        stream_id=stream_id,
        status=stream["status"],
        current_url=stream["current_url"],
        start_time=stream["start_time"],
        last_action=stream["last_action"]
    )

@app.get("/mcp/streams")
async def list_active_streams():
    """List all active streams"""
    return {
        "total_streams": len(active_streams),
        "streams": [
            {
                "stream_id": stream_id,
                "status": stream["status"],
                "current_url": stream["current_url"],
                "is_recording": stream.get("is_recording", False)
            }
            for stream_id, stream in active_streams.items()
        ]
    }

@app.get("/mcp/records/{stream_id}")
async def get_stream_records(stream_id: str):
    """Recording history for a specific stream"""
    if stream_id not in stream_records:
        return {"records": []}
    
    return {"records": stream_records[stream_id]}

@app.get("/")
def read_root():
    return {
        "service": "mcp_server",
        "status": "running",
        "endpoints": {
            "control": "/mcp/control",
            "ai_trigger": "/mcp/ai-trigger",
            "status": "/mcp/status/{stream_id}",
            "streams": "/mcp/streams",
            "records": "/mcp/records/{stream_id}"
        }
    }
