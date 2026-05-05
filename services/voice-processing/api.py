"""
Kirobi Voice Processing API
FastAPI service for voice interaction
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from voice_interface import VoiceInterface, VoiceConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Kirobi Voice Processing API",
    description="Speech-to-Text and Text-to-Speech services",
    version="1.0.0"
)

# Initialize voice interface
voice_config = VoiceConfig()
voice_interface = VoiceInterface(voice_config)


@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    logger.info("Starting Voice Processing API...")
    voice_interface.initialize()
    logger.info("Voice Processing API ready!")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "voice-processing",
        "timestamp": datetime.now().isoformat()
    }


class TranscribeRequest(BaseModel):
    """Request model for transcription"""
    language: Optional[str] = "de"


class TranscribeResponse(BaseModel):
    """Response model for transcription"""
    text: str
    language: str
    language_probability: float
    duration: float
    processing_time: float
    segments: list


class SynthesizeRequest(BaseModel):
    """Request model for TTS"""
    text: str
    language: Optional[str] = "de"


class SynthesizeResponse(BaseModel):
    """Response model for TTS"""
    audio_url: str
    text: str
    duration: float


@app.post("/stt/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    language: Optional[str] = "de"
):
    """
    Transcribe audio file to text

    - **audio_file**: Audio file (WAV, MP3, etc.)
    - **language**: Language code (de, en, etc.)
    """
    try:
        # Save uploaded file
        temp_path = f"/tmp/upload_{datetime.now().timestamp()}.wav"
        with open(temp_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)

        # Transcribe
        result = voice_interface.stt.transcribe_audio(temp_path, language)

        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return TranscribeResponse(**result)

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tts/synthesize", response_model=SynthesizeResponse)
async def synthesize_speech(request: SynthesizeRequest):
    """
    Synthesize speech from text

    - **text**: Text to synthesize
    - **language**: Language code (currently only 'de' supported)
    """
    try:
        # Synthesize
        output_path = f"/data/tts_{datetime.now().timestamp()}.wav"
        audio_path = voice_interface.tts.synthesize(request.text, output_path)

        # Get audio info
        import soundfile as sf
        info = sf.info(audio_path)

        return SynthesizeResponse(
            audio_url=f"/audio/{Path(audio_path).name}",
            text=request.text,
            duration=info.duration
        )

    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """
    Retrieve generated audio file

    - **filename**: Audio filename
    """
    audio_path = f"/data/{filename}"

    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        audio_path,
        media_type="audio/wav",
        filename=filename
    )


class ConversationStartRequest(BaseModel):
    """Request to start conversation"""
    participant: str
    greeting: Optional[str] = None
    language: Optional[str] = "de"


class ConversationStartResponse(BaseModel):
    """Response for conversation start"""
    session_id: str
    participant: str
    status: str
    greeting_audio_url: Optional[str] = None


@app.post("/conversation/start", response_model=ConversationStartResponse)
async def start_conversation(request: ConversationStartRequest, background_tasks: BackgroundTasks):
    """
    Start a new voice conversation session

    - **participant**: Name of participant (Sven, Samira, Sineo)
    - **greeting**: Optional greeting message
    - **language**: Language code
    """
    try:
        session_id = f"session_{datetime.now().timestamp()}"

        # Set participant
        voice_interface.memory.participant = request.participant

        # Synthesize greeting if provided
        greeting_audio_url = None
        if request.greeting:
            audio_path = voice_interface.tts.synthesize(request.greeting)
            greeting_audio_url = f"/audio/{Path(audio_path).name}"

        return ConversationStartResponse(
            session_id=session_id,
            participant=request.participant,
            status="active",
            greeting_audio_url=greeting_audio_url
        )

    except Exception as e:
        logger.error(f"Conversation start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversation/status/{session_id}")
async def get_conversation_status(session_id: str):
    """
    Get status of conversation session

    - **session_id**: Session identifier
    """
    # TODO: Implement session tracking
    return {
        "session_id": session_id,
        "status": "active",
        "exchanges": len(voice_interface.memory.exchanges)
    }


@app.post("/conversation/end/{session_id}")
async def end_conversation(session_id: str):
    """
    End conversation and save session

    - **session_id**: Session identifier
    """
    try:
        # Save session
        session_file = f"/data/conversations/{session_id}.json"
        voice_interface.memory.save_session(session_file)

        return {
            "session_id": session_id,
            "status": "ended",
            "session_file": session_file,
            "total_exchanges": len(voice_interface.memory.exchanges)
        }

    except Exception as e:
        logger.error(f"Conversation end error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models/info")
async def get_models_info():
    """Get information about loaded models"""
    return {
        "stt": {
            "model": voice_config.WHISPER_MODEL,
            "device": voice_config.WHISPER_DEVICE,
            "compute_type": voice_config.WHISPER_COMPUTE_TYPE
        },
        "tts": {
            "model": voice_config.PIPER_MODEL_PATH,
            "language": voice_config.DEFAULT_LANGUAGE
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
