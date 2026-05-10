"""
Kirobi Voice Processing API
FastAPI service for voice interaction
"""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Request, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import asyncio
import json
import re

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

    SAMPLES_PATH = Path(os.getenv("VOICE_SAMPLES_PATH", "/data/voice-samples"))
    SAMPLES_PATH.mkdir(parents=True, exist_ok=True)
    app.state.samples_path = SAMPLES_PATH

    # Voice Profiles Tabelle
    try:
        import asyncpg as _asyncpg
        DATABASE_URL_VP = (
            f"postgresql://{os.getenv('POSTGRES_USER', 'kirobi')}"
            f":{os.getenv('POSTGRES_PASSWORD', 'changeme')}"
            f"@{os.getenv('POSTGRES_HOST', 'postgres')}"
            f":{os.getenv('POSTGRES_PORT', '5432')}"
            f"/{os.getenv('POSTGRES_DB', 'kirobi')}"
        )
        _vp_pool = await _asyncpg.create_pool(DATABASE_URL_VP, min_size=1, max_size=4)
        await _vp_pool.execute("""
            CREATE TABLE IF NOT EXISTS voice_profiles (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                description TEXT DEFAULT '',
                language    TEXT DEFAULT 'de_DE',
                piper_voice TEXT DEFAULT 'de_DE-thorsten-high',
                gender      TEXT DEFAULT 'neutral',
                speed       DOUBLE PRECISION DEFAULT 1.0,
                pitch       DOUBLE PRECISION DEFAULT 0.0,
                created_at  TIMESTAMPTZ DEFAULT NOW(),
                updated_at  TIMESTAMPTZ DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS voice_profile_samples (
                id          TEXT PRIMARY KEY,
                profile_id  TEXT NOT NULL REFERENCES voice_profiles(id) ON DELETE CASCADE,
                filename    TEXT NOT NULL,
                file_path   TEXT NOT NULL,
                reference_text TEXT DEFAULT '',
                duration_s  DOUBLE PRECISION DEFAULT 0,
                created_at  TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        app.state.vp_pool = _vp_pool
        logger.info("Voice profile DB pool initialized")
    except Exception as _exc:  # noqa: BLE001
        logger.warning("Voice profile DB not available: %s", _exc)
        app.state.vp_pool = None

    logger.info("Voice Processing API ready!")


@app.on_event("shutdown")
async def shutdown_event():
    pool = getattr(app.state, "vp_pool", None)
    if pool is not None:
        await pool.close()
        app.state.vp_pool = None


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
    voice: Optional[str] = None
    tone: Optional[str] = "neutral"
    speed: Optional[float] = 1.0


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
        chosen_voice = None
        if request.voice:
            chosen_voice = find_voice(request.voice)
            if chosen_voice is None or chosen_voice.voice_id != request.voice:
                raise HTTPException(status_code=404, detail="TTS-Stimme nicht gefunden")

        tone_preset = get_tone(request.tone or "neutral")
        spoken_text = apply_tone_to_text(request.text, tone_preset)

        output_path = f"/data/tts_{datetime.now().timestamp()}.wav"
        audio_path = voice_interface.tts.synthesize(
            spoken_text,
            output_path,
            voice_onnx=chosen_voice.onnx_path if chosen_voice else None,
            voice_config=chosen_voice.config_path if chosen_voice else None,
        )

        import soundfile as sf
        info = sf.info(audio_path)

        return SynthesizeResponse(
            audio_url=f"/audio/{Path(audio_path).name}",
            text=request.text,
            duration=info.duration
        )

    except HTTPException:
        raise
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


# =============================================================================
# Voice catalog & persona presets
# =============================================================================
from voices import list_voices, find_voice, default_voice  # noqa: E402
from personas import list_tones, get_tone, apply_tone_to_text  # noqa: E402


@app.get("/voices")
async def get_voices():
    """List all available Piper TTS voices."""
    return {"voices": [v.to_dict() for v in list_voices()]}


@app.get("/personas")
async def get_personas():
    """List all available tone presets (layered on top of agent personas)."""
    return {"tones": [t.to_dict() for t in list_tones()]}


# =============================================================================
# Multi-turn conversation endpoint with memory
# =============================================================================
import httpx  # noqa: E402
from kirobi_bridge import ensure_conversation, send_message  # noqa: E402


@app.post("/conversation/turn")
async def conversation_turn(
    audio_file: UploadFile = File(...),
    conversation_id: Optional[str] = None,
    agent: str = "kirobi",
    tone: str = "neutral",
    voice: Optional[str] = None,
    language: str = "de",
):
    """One full voice-conversation turn with persistent memory.

    1. STT: transcribe uploaded audio.
    2. LLM: post the transcript to the kirobi-api `/conversations/{id}/messages`
       endpoint. The API attaches the agent system prompt + the tone modifier
       and uses the existing conversation history for memory.
    3. TTS: synthesize the assistant reply with the chosen Piper voice.

    Returns conversation_id (re-use for continuous chat), transcript, reply text,
    and a URL to the synthesized audio.
    """
    # ---- 1. STT ----
    temp_in = f"/tmp/voice_turn_{int(datetime.now().timestamp() * 1000)}.wav"
    try:
        with open(temp_in, "wb") as fh:
            fh.write(await audio_file.read())
        stt_result = voice_interface.stt.transcribe_audio(temp_in, language)
        transcript = (stt_result.get("text") or "").strip()
    finally:
        if os.path.exists(temp_in):
            os.remove(temp_in)

    if not transcript:
        raise HTTPException(status_code=400, detail="STT lieferte leeren Text")

    # ---- 2. LLM via API (with memory) ----
    tone_preset = get_tone(tone)
    try:
        async with httpx.AsyncClient() as client:
            conv_id = await ensure_conversation(
                client=client,
                conversation_id=conversation_id,
                title=f"Voice {agent}",
                agent=agent,
            )
            assistant = await send_message(
                client=client,
                conversation_id=conv_id,
                text=transcript,
                agent=agent,
                extra_system=tone_preset.modifier,
            )
    except httpx.HTTPStatusError as exc:
        # Conversation may have vanished — try a fresh one once.
        if exc.response.status_code == 404 and conversation_id:
            async with httpx.AsyncClient() as client:
                conv_id = await ensure_conversation(
                    client=client,
                    conversation_id=None,
                    title=f"Voice {agent}",
                    agent=agent,
                )
                assistant = await send_message(
                    client=client,
                    conversation_id=conv_id,
                    text=transcript,
                    agent=agent,
                    extra_system=tone_preset.modifier,
                )
        else:
            logger.error("API call failed: %s", exc)
            raise HTTPException(status_code=502, detail=f"API-Fehler: {exc}")
    except Exception as exc:  # noqa: BLE001
        logger.error("LLM bridge failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    reply_text_full = assistant.get("content") or assistant.get("text") or ""
    reply_text_tts = apply_tone_to_text(reply_text_full, tone_preset)

    # ---- 3. TTS with chosen voice ----
    chosen = find_voice(voice) or default_voice()
    if chosen is None:
        raise HTTPException(status_code=503, detail="Keine TTS-Stimme verfuegbar")

    out_path = f"/data/voice_turn_{int(datetime.now().timestamp() * 1000)}.wav"
    try:
        voice_interface.tts.synthesize(
            reply_text_tts,
            output_path=out_path,
            voice_onnx=chosen.onnx_path,
            voice_config=chosen.config_path,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("TTS failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"TTS-Fehler: {exc}")

    return {
        "conversation_id": conv_id,
        "transcript": transcript,
        "reply_text": reply_text_full,
        "reply_text_tts": reply_text_tts,
        "audio_url": f"/audio/{Path(out_path).name}",
        "agent": agent,
        "tone": tone_preset.tone_id,
        "voice": chosen.voice_id,
        "model": assistant.get("model"),
    }


# =============================================================================
# Voice-Conversation v2 — streaming WebSocket
# =============================================================================
# Protocol (client <-> server, all JSON unless noted):
#   1. Client connects to /conversation/ws
#   2. Client sends JSON config:
#        {"type":"config","agent":"kirobi","tone":"neutral","voice":null,
#         "language":"de","conversation_id":null,"jwt":"<token>"}
#   3. Client sends ONE binary frame containing the full WAV/webm audio blob
#   4. Server emits events as JSON text frames:
#        {"event":"transcript","text":"..."}
#        {"event":"text_chunk","delta":"..."}
#        {"event":"audio_chunk","seq":1,"url":"/audio/voice_ws_xxx.wav","text":"..."}
#        {"event":"done","conversation_id":"...","reply_text":"...","chunks":N}
#        {"event":"error","detail":"..."}
#   5. Server closes the socket.

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[\.!\?\n])\s+")
_MIN_SENTENCE_CHARS = 30  # don't TTS micro-fragments


def _flush_sentences(buffer: str, force: bool = False) -> tuple[list[str], str]:
    """Split *buffer* on sentence boundaries.

    Returns (complete_sentences, remainder). If *force* is True, returns the
    whole buffer as a final sentence (used at end of stream).
    """
    if force:
        text = buffer.strip()
        return ([text] if text else [], "")
    parts = _SENTENCE_SPLIT_RE.split(buffer)
    if len(parts) < 2:
        return ([], buffer)
    *complete, remainder = parts
    out: list[str] = []
    pending = ""
    for piece in complete:
        pending = (pending + " " + piece).strip() if pending else piece.strip()
        if len(pending) >= _MIN_SENTENCE_CHARS:
            out.append(pending)
            pending = ""
    if pending:
        # carry the still-too-short prefix forward
        remainder = (pending + " " + remainder).strip()
    return out, remainder


@app.websocket("/conversation/ws")
async def conversation_ws(ws: WebSocket):
    """Streaming voice conversation: STT → SSE-LLM-stream → sentence-level TTS."""
    await ws.accept()
    seq = 0
    full_reply_parts: list[str] = []

    async def send_event(payload: dict):
        try:
            await ws.send_text(json.dumps(payload))
        except Exception:  # noqa: BLE001
            pass

    try:
        # ---- 1. Receive config ----
        config_raw = await ws.receive_text()
        try:
            config = json.loads(config_raw)
        except json.JSONDecodeError:
            await send_event({"event": "error", "detail": "first frame must be JSON config"})
            await ws.close()
            return
        if config.get("type") != "config":
            await send_event({"event": "error", "detail": "first frame must have type=config"})
            await ws.close()
            return

        agent = (config.get("agent") or "kirobi").strip()
        tone = (config.get("tone") or "neutral").strip()
        voice_id = config.get("voice")
        language = (config.get("language") or "de").strip()
        conversation_id = config.get("conversation_id")
        jwt = config.get("jwt")
        mode = (config.get("mode") or "oneshot").strip()

        # ---- 2. Receive audio ----
        # oneshot:  ONE binary frame containing the full webm/wav blob.
        # chunked:  N binary frames (live MediaRecorder chunks) terminated by JSON {"type":"end"}.
        audio_bytes: bytes
        if mode == "chunked":
            buf = bytearray()
            max_bytes = 50 * 1024 * 1024  # 50 MB hard cap
            while True:
                msg = await ws.receive()
                if msg.get("type") == "websocket.disconnect":
                    return
                if "bytes" in msg and msg["bytes"] is not None:
                    buf.extend(msg["bytes"])
                    if len(buf) > max_bytes:
                        await send_event({"event": "error", "detail": "audio too large (>50 MB)"})
                        await ws.close()
                        return
                    continue
                if "text" in msg and msg["text"] is not None:
                    try:
                        ctrl = json.loads(msg["text"])
                    except json.JSONDecodeError:
                        continue
                    if ctrl.get("type") == "end":
                        break
            if not buf:
                await send_event({"event": "error", "detail": "no audio received"})
                await ws.close()
                return
            audio_bytes = bytes(buf)
        else:
            audio_msg = await ws.receive()
            audio_bytes = audio_msg.get("bytes")
            if not audio_bytes:
                await send_event({"event": "error", "detail": "second frame must be binary audio"})
                await ws.close()
                return

        temp_in = f"/tmp/voice_ws_{int(datetime.now().timestamp() * 1000)}.wav"
        try:
            with open(temp_in, "wb") as fh:
                fh.write(audio_bytes)
            stt_result = voice_interface.stt.transcribe_audio(temp_in, language)
        finally:
            if os.path.exists(temp_in):
                os.remove(temp_in)

        transcript = (stt_result.get("text") or "").strip()
        if not transcript:
            await send_event({"event": "error", "detail": "STT lieferte leeren Text"})
            await ws.close()
            return
        await send_event({"event": "transcript", "text": transcript})

        tone_preset = get_tone(tone)
        chosen_voice = find_voice(voice_id) or default_voice()
        if chosen_voice is None:
            await send_event({"event": "error", "detail": "Keine TTS-Stimme verfuegbar"})
            await ws.close()
            return

        # ---- 3. Ensure conversation in api ----
        api_url = os.getenv("KIROBI_API_URL", "http://api:8000").rstrip("/")
        auth_url = os.getenv("AUTH_SERVICE_URL", "http://auth:8000").rstrip("/")
        async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=10.0)) as client:
            # JWT: prefer client-supplied; fall back to bridge service-account login
            if jwt:
                token = jwt
            else:
                from kirobi_bridge import _login as _bridge_login  # type: ignore
                token = await _bridge_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            # Ensure conversation belongs to the *current* token's user
            conv_id = conversation_id
            if conv_id:
                check = await client.get(f"{api_url}/conversations/{conv_id}", headers=headers, timeout=8.0)
                if check.status_code != 200:
                    conv_id = None
            if not conv_id:
                create = await client.post(
                    f"{api_url}/conversations",
                    json={"title": f"Voice {agent}", "agent": agent},
                    headers=headers,
                    timeout=10.0,
                )
                if create.status_code >= 400:
                    await send_event({"event": "error", "detail": f"create conversation failed: HTTP {create.status_code} {create.text[:200]}"})
                    await ws.close()
                    return
                conv_id = create.json()["id"]

            # ---- 4. Stream LLM via api SSE endpoint ----
            payload = {
                "content": transcript,
                "agent": agent,
                "system_prompt_extra": tone_preset.modifier or None,
            }
            buffer = ""
            persisted_reply = ""
            try:
                async with client.stream(
                    "POST",
                    f"{api_url}/conversations/{conv_id}/messages/stream",
                    json=payload,
                    headers=headers,
                ) as resp:
                    if resp.status_code != 200:
                        body = await resp.aread()
                        await send_event({"event": "error", "detail": f"api stream HTTP {resp.status_code}: {body[:300].decode(errors='replace')}"})
                        await ws.close()
                        return
                    async for raw_line in resp.aiter_lines():
                        if not raw_line or not raw_line.startswith("data:"):
                            continue
                        try:
                            evt = json.loads(raw_line[5:].strip())
                        except json.JSONDecodeError:
                            continue
                        if evt.get("event") == "delta":
                            delta = evt.get("text", "")
                            if not delta:
                                continue
                            buffer += delta
                            full_reply_parts.append(delta)
                            await send_event({"event": "text_chunk", "delta": delta})

                            sentences, buffer = _flush_sentences(buffer)
                            for sentence in sentences:
                                seq += 1
                                spoken = apply_tone_to_text(sentence, tone_preset)
                                out_path = f"/data/voice_ws_{int(datetime.now().timestamp() * 1000)}_{seq}.wav"
                                try:
                                    voice_interface.tts.synthesize(
                                        spoken,
                                        output_path=out_path,
                                        voice_onnx=chosen_voice.onnx_path,
                                        voice_config=chosen_voice.config_path,
                                    )
                                    await send_event({
                                        "event": "audio_chunk",
                                        "seq": seq,
                                        "url": f"/audio/{Path(out_path).name}",
                                        "text": sentence,
                                    })
                                except Exception as exc:  # noqa: BLE001
                                    await send_event({"event": "error", "detail": f"TTS failed seq={seq}: {exc}"})
                        elif evt.get("event") == "done":
                            persisted_reply = evt.get("content") or "".join(full_reply_parts)
                        elif evt.get("event") == "error":
                            await send_event({"event": "error", "detail": evt.get("detail", "upstream error")})
            except httpx.HTTPError as exc:
                await send_event({"event": "error", "detail": f"api stream error: {exc}"})
                await ws.close()
                return

            # Flush any tail
            tail_sentences, _ = _flush_sentences(buffer, force=True)
            for sentence in tail_sentences:
                seq += 1
                spoken = apply_tone_to_text(sentence, tone_preset)
                out_path = f"/data/voice_ws_{int(datetime.now().timestamp() * 1000)}_{seq}.wav"
                try:
                    voice_interface.tts.synthesize(
                        spoken,
                        output_path=out_path,
                        voice_onnx=chosen_voice.onnx_path,
                        voice_config=chosen_voice.config_path,
                    )
                    await send_event({
                        "event": "audio_chunk",
                        "seq": seq,
                        "url": f"/audio/{Path(out_path).name}",
                        "text": sentence,
                    })
                except Exception as exc:  # noqa: BLE001
                    await send_event({"event": "error", "detail": f"TTS failed seq={seq}: {exc}"})

            await send_event({
                "event": "done",
                "conversation_id": conv_id,
                "reply_text": persisted_reply or "".join(full_reply_parts),
                "chunks": seq,
                "voice": chosen_voice.voice_id,
                "tone": tone_preset.tone_id,
                "agent": agent,
            })
    except WebSocketDisconnect:
        logger.info("voice WS client disconnected")
        return
    except Exception as exc:  # noqa: BLE001
        logger.exception("voice WS error: %s", exc)
        await send_event({"event": "error", "detail": str(exc)})
    finally:
        try:
            await ws.close()
        except Exception:  # noqa: BLE001
            pass


# ─────────────────────────────────────────────────────────────
# Voice Profiles  (Voicebox-kompatible API)
# ─────────────────────────────────────────────────────────────
class VoiceProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    description: str = Field("", max_length=256)
    language: str = Field("de_DE", max_length=16)
    piper_voice: str = Field("de_DE-thorsten-high", max_length=64)
    gender: str = Field("neutral", max_length=16)
    speed: float = Field(1.0, ge=0.5, le=2.0)
    pitch: float = Field(0.0, ge=-10.0, le=10.0)


class VoiceProfileResponse(BaseModel):
    id: str
    name: str
    description: str
    language: str
    piper_voice: str
    gender: str
    speed: float
    pitch: float
    sample_count: int
    created_at: str
    updated_at: str


def _get_vp_pool(request: Request):
    pool = getattr(request.app.state, "vp_pool", None)
    if pool is None:
        raise HTTPException(503, "Voice profile DB nicht verfügbar")
    return pool


@app.get("/profiles")
async def list_profiles(request: Request):
    """Alle Voice-Profile mit Sample-Count."""
    pool = _get_vp_pool(request)
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT vp.*,
                   COALESCE((SELECT COUNT(*) FROM voice_profile_samples vps WHERE vps.profile_id = vp.id), 0) AS sample_count
            FROM voice_profiles vp
            ORDER BY vp.created_at DESC
        """)
    return [
        {**dict(r), "created_at": r["created_at"].isoformat(), "updated_at": r["updated_at"].isoformat()}
        for r in rows
    ]


@app.post("/profiles", status_code=201)
async def create_profile(request: Request, body: VoiceProfileCreate):
    """Neues Voice-Profil anlegen."""
    pool = _get_vp_pool(request)
    profile_id = str(uuid.uuid4())
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO voice_profiles (id, name, description, language, piper_voice, gender, speed, pitch)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
        """, profile_id, body.name, body.description, body.language, body.piper_voice, body.gender, body.speed, body.pitch)
        row = await conn.fetchrow("SELECT * FROM voice_profiles WHERE id=$1", profile_id)
    return {**dict(row), "created_at": row["created_at"].isoformat(), "updated_at": row["updated_at"].isoformat(), "sample_count": 0}


@app.get("/profiles/{profile_id}")
async def get_profile(profile_id: str, request: Request):
    pool = _get_vp_pool(request)
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT vp.*,
                   COALESCE((SELECT COUNT(*) FROM voice_profile_samples vps WHERE vps.profile_id = vp.id), 0) AS sample_count
            FROM voice_profiles vp WHERE vp.id = $1
        """, profile_id)
    if not row:
        raise HTTPException(status_code=404, detail="Profil nicht gefunden")
    return {**dict(row), "created_at": row["created_at"].isoformat(), "updated_at": row["updated_at"].isoformat()}


@app.put("/profiles/{profile_id}")
async def update_profile(profile_id: str, request: Request, body: VoiceProfileCreate):
    pool = _get_vp_pool(request)
    async with pool.acquire() as conn:
        exists = await conn.fetchval("SELECT id FROM voice_profiles WHERE id=$1", profile_id)
        if not exists:
            raise HTTPException(404, "Profil nicht gefunden")
        await conn.execute("""
            UPDATE voice_profiles
            SET name=$2, description=$3, language=$4, piper_voice=$5, gender=$6, speed=$7, pitch=$8, updated_at=NOW()
            WHERE id=$1
        """, profile_id, body.name, body.description, body.language, body.piper_voice, body.gender, body.speed, body.pitch)
        row = await conn.fetchrow("SELECT * FROM voice_profiles WHERE id=$1", profile_id)
        count = await conn.fetchval("SELECT COUNT(*) FROM voice_profile_samples WHERE profile_id=$1", profile_id)
    return {**dict(row), "created_at": row["created_at"].isoformat(), "updated_at": row["updated_at"].isoformat(), "sample_count": count}


@app.delete("/profiles/{profile_id}", status_code=204)
async def delete_profile(profile_id: str, request: Request):
    pool = _get_vp_pool(request)
    async with pool.acquire() as conn:
        sample_paths = await conn.fetch("SELECT file_path FROM voice_profile_samples WHERE profile_id=$1", profile_id)
        exists = await conn.fetchval("SELECT id FROM voice_profiles WHERE id=$1", profile_id)
        if not exists:
            raise HTTPException(404, "Profil nicht gefunden")
        await conn.execute("DELETE FROM voice_profiles WHERE id=$1", profile_id)
    for sample in sample_paths:
        try:
            Path(sample["file_path"]).unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass
    profile_dir = getattr(request.app.state, "samples_path", Path("/data/voice-samples")) / profile_id
    try:
        profile_dir.rmdir()
    except Exception:  # noqa: BLE001
        pass


@app.get("/profiles/{profile_id}/samples")
async def list_samples(profile_id: str, request: Request):
    pool = _get_vp_pool(request)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM voice_profile_samples WHERE profile_id=$1 ORDER BY created_at DESC",
            profile_id
        )
    return [
        {**dict(r), "created_at": r["created_at"].isoformat()}
        for r in rows
    ]


@app.post("/profiles/{profile_id}/samples", status_code=201)
async def add_sample(
    profile_id: str,
    request: Request,
    file: UploadFile = File(...),
    reference_text: str = Form(""),
):
    """Lädt eine Audio-Referenz-Datei für ein Profil hoch."""
    pool = _get_vp_pool(request)
    async with pool.acquire() as conn:
        exists = await conn.fetchval("SELECT id FROM voice_profiles WHERE id=$1", profile_id)
    if not exists:
        raise HTTPException(404, "Profil nicht gefunden")

    sample_id = str(uuid.uuid4())
    samples_dir = getattr(request.app.state, "samples_path", Path("/data/voice-samples"))
    profile_dir = samples_dir / profile_id
    profile_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "sample.wav").suffix.lower() or ".wav"
    file_path = profile_dir / f"{sample_id}{suffix}"
    content = await file.read()
    file_path.write_bytes(content)

    duration_s = 0.0
    try:
        import wave
        if suffix == ".wav":
            with wave.open(str(file_path), "rb") as wf:
                duration_s = wf.getnframes() / wf.getframerate()
    except Exception:  # noqa: BLE001
        pass

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO voice_profile_samples (id, profile_id, filename, file_path, reference_text, duration_s)
            VALUES ($1,$2,$3,$4,$5,$6)
        """, sample_id, profile_id, file.filename or f"{sample_id}{suffix}", str(file_path), reference_text, duration_s)
        row = await conn.fetchrow("SELECT * FROM voice_profile_samples WHERE id=$1", sample_id)

    return {**dict(row), "created_at": row["created_at"].isoformat()}


@app.delete("/profiles/{profile_id}/samples/{sample_id}", status_code=204)
async def delete_sample(profile_id: str, sample_id: str, request: Request):
    pool = _get_vp_pool(request)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT file_path FROM voice_profile_samples WHERE id=$1 AND profile_id=$2",
            sample_id, profile_id
        )
        if not row:
            raise HTTPException(404, "Sample nicht gefunden")
        await conn.execute("DELETE FROM voice_profile_samples WHERE id=$1", sample_id)
    try:
        Path(row["file_path"]).unlink(missing_ok=True)
    except Exception:  # noqa: BLE001
        pass


@app.post("/profiles/{profile_id}/generate")
async def generate_with_profile(profile_id: str, request: Request, body: SynthesizeRequest):
    """Generiert Audio mit einem Voice-Profil (überschreibt voice/speed mit Profil-Werten)."""
    pool = _get_vp_pool(request)
    async with pool.acquire() as conn:
        profile = await conn.fetchrow("SELECT * FROM voice_profiles WHERE id=$1", profile_id)
    if not profile:
        raise HTTPException(404, "Profil nicht gefunden")

    override = SynthesizeRequest(
        text=body.text,
        language=body.language,
        voice=profile["piper_voice"],
        tone=body.tone,
        speed=profile["speed"],
    )
    return await synthesize_speech(override)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
