"""
Kirobi Voice Interface System
Natural language voice interaction with local STT/TTS

Features:
- Local Whisper (faster-whisper) for Speech-to-Text
- Piper TTS for high-quality Text-to-Speech
- CUDA acceleration for NVIDIA GPUs
- Conversation context and memory
- Multi-speaker support
- German and English language support
"""

import asyncio
import json
import logging
import os
import queue
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

import numpy as np
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VoiceConfig:
    """Configuration for voice interface"""

    # Audio settings
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = 'int16'

    # Voice Activity Detection
    SILENCE_THRESHOLD = 0.01
    SILENCE_DURATION = 1.5  # seconds of silence before stopping
    MIN_RECORDING_DURATION = 0.5  # minimum recording length
    MAX_RECORDING_DURATION = 60  # maximum recording length

    # Model paths (set via environment or defaults)
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'large-v3')
    WHISPER_DEVICE = os.getenv('WHISPER_DEVICE', 'cuda')  # 'cuda' or 'cpu'
    WHISPER_COMPUTE_TYPE = os.getenv('WHISPER_COMPUTE_TYPE', 'float16')  # or 'int8'

    # Piper TTS
    PIPER_MODEL_PATH = os.getenv('PIPER_MODEL_PATH', '/models/piper/de_DE-thorsten-high.onnx')
    PIPER_CONFIG_PATH = os.getenv('PIPER_CONFIG_PATH', '/models/piper/de_DE-thorsten-high.onnx.json')

    # Language
    DEFAULT_LANGUAGE = os.getenv('VOICE_LANGUAGE', 'de')  # 'de' or 'en'

    # Conversation
    CONTEXT_MEMORY_SIZE = 10  # remember last N exchanges


class WhisperSTT:
    """Speech-to-Text using faster-whisper with CUDA acceleration"""

    def __init__(self, config: VoiceConfig):
        self.config = config
        self.model = None
        logger.info(f"Initializing Whisper STT with model: {config.WHISPER_MODEL}")

    def load_model(self):
        """Load Whisper model"""
        try:
            self.model = WhisperModel(
                self.config.WHISPER_MODEL,
                device=self.config.WHISPER_DEVICE,
                compute_type=self.config.WHISPER_COMPUTE_TYPE
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def transcribe_audio(self, audio_path: str, language: Optional[str] = None) -> Dict:
        """
        Transcribe audio file to text

        Args:
            audio_path: Path to audio file
            language: Language code ('de', 'en', etc.)

        Returns:
            Dictionary with transcription and metadata
        """
        if not self.model:
            self.load_model()

        try:
            start_time = time.time()

            segments, info = self.model.transcribe(
                audio_path,
                language=language or self.config.DEFAULT_LANGUAGE,
                vad_filter=True,  # Voice Activity Detection
                vad_parameters=dict(
                    threshold=0.5,
                    min_speech_duration_ms=250,
                    max_speech_duration_s=float('inf'),
                    min_silence_duration_ms=2000,
                    speech_pad_ms=400
                )
            )

            # Collect all segments
            text_segments = []
            for segment in segments:
                text_segments.append({
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text.strip()
                })

            full_text = " ".join([seg['text'] for seg in text_segments])

            elapsed_time = time.time() - start_time

            result = {
                'text': full_text,
                'language': info.language,
                'language_probability': info.language_probability,
                'duration': info.duration,
                'segments': text_segments,
                'processing_time': elapsed_time
            }

            logger.info(f"Transcribed in {elapsed_time:.2f}s: {full_text[:100]}...")
            return result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def transcribe_numpy(self, audio_data: np.ndarray, language: Optional[str] = None) -> Dict:
        """
        Transcribe numpy audio array

        Args:
            audio_data: Numpy array of audio samples
            language: Language code

        Returns:
            Dictionary with transcription
        """
        # Save to temporary file
        temp_path = f"/tmp/kirobi_voice_{int(time.time())}.wav"
        sf.write(temp_path, audio_data, self.config.SAMPLE_RATE)

        try:
            result = self.transcribe_audio(temp_path, language)
            return result
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)


class PiperTTS:
    """Text-to-Speech using Piper"""

    def __init__(self, config: VoiceConfig):
        self.config = config
        self.model_path = Path(config.PIPER_MODEL_PATH)
        self.config_path = Path(config.PIPER_CONFIG_PATH)
        logger.info(f"Initializing Piper TTS with model: {self.model_path}")

    def synthesize(self, text: str, output_path: Optional[str] = None, voice_onnx: Optional[str] = None, voice_config: Optional[str] = None) -> str:
        """
        Synthesize speech from text

        Args:
            text: Text to speak
            output_path: Output audio file path (auto-generated if None)
            voice_onnx: Override path to .onnx voice model (defaults to configured voice)
            voice_config: Override path to .onnx.json config

        Returns:
            Path to generated audio file
        """
        if not output_path:
            output_path = f"/tmp/kirobi_tts_{int(time.time())}.wav"

        model_path = voice_onnx or str(self.model_path)
        config_path = voice_config or str(self.config_path)

        try:
            # Run piper command
            import subprocess

            cmd = [
                "piper",
                "--model", model_path,
                "--config", config_path,
                "--output_file", output_path
            ]

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(input=text)

            if process.returncode != 0:
                logger.error(f"Piper TTS failed: {stderr}")
                raise Exception(f"TTS synthesis failed: {stderr}")

            logger.info(f"TTS synthesized: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            raise

    def speak(self, text: str) -> None:
        """
        Synthesize and play audio immediately

        Args:
            text: Text to speak
        """
        audio_path = self.synthesize(text)

        try:
            # Play audio
            data, samplerate = sf.read(audio_path)
            sd.play(data, samplerate)
            sd.wait()
        finally:
            # Cleanup
            if os.path.exists(audio_path):
                os.remove(audio_path)


class AudioRecorder:
    """Record audio from microphone with VAD"""

    def __init__(self, config: VoiceConfig):
        self.config = config
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.stream = None

    def audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream"""
        if status:
            logger.warning(f"Audio callback status: {status}")
        self.audio_queue.put(indata.copy())

    def record_until_silence(self) -> np.ndarray:
        """
        Record audio until silence is detected

        Returns:
            Numpy array of audio samples
        """
        logger.info("Recording started... (speak now)")

        audio_chunks = []
        silence_chunks = 0
        max_silence_chunks = int(
            self.config.SILENCE_DURATION * self.config.SAMPLE_RATE / 1024
        )

        self.is_recording = True

        with sd.InputStream(
            samplerate=self.config.SAMPLE_RATE,
            channels=self.config.CHANNELS,
            dtype=self.config.DTYPE,
            callback=self.audio_callback,
            blocksize=1024
        ):
            start_time = time.time()

            while self.is_recording:
                try:
                    # Get audio chunk with timeout
                    chunk = self.audio_queue.get(timeout=0.1)
                    audio_chunks.append(chunk)

                    # Check for silence
                    audio_level = np.abs(chunk).mean()

                    if audio_level < self.config.SILENCE_THRESHOLD:
                        silence_chunks += 1
                    else:
                        silence_chunks = 0

                    # Stop conditions
                    elapsed = time.time() - start_time

                    if silence_chunks >= max_silence_chunks and elapsed > self.config.MIN_RECORDING_DURATION:
                        logger.info("Silence detected, stopping recording")
                        break

                    if elapsed > self.config.MAX_RECORDING_DURATION:
                        logger.info("Max recording duration reached")
                        break

                except queue.Empty:
                    continue

        if not audio_chunks:
            raise ValueError("No audio recorded")

        # Concatenate all chunks
        audio_data = np.concatenate(audio_chunks, axis=0)
        logger.info(f"Recording complete: {len(audio_data)/self.config.SAMPLE_RATE:.2f}s")

        return audio_data.flatten()

    def stop(self):
        """Stop recording"""
        self.is_recording = False


class ConversationMemory:
    """Manage conversation context and history"""

    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.exchanges: List[Dict] = []
        self.session_start = datetime.now()
        self.participant = None

    def add_exchange(self, user_text: str, assistant_text: str):
        """Add a conversation exchange"""
        exchange = {
            'timestamp': datetime.now().isoformat(),
            'user': user_text,
            'assistant': assistant_text
        }
        self.exchanges.append(exchange)

        # Keep only last N exchanges
        if len(self.exchanges) > self.max_size:
            self.exchanges = self.exchanges[-self.max_size:]

    def get_context(self) -> str:
        """Get conversation context as formatted string"""
        if not self.exchanges:
            return ""

        context_lines = ["Previous conversation:"]
        for ex in self.exchanges[-5:]:  # Last 5 exchanges
            context_lines.append(f"User: {ex['user']}")
            context_lines.append(f"Assistant: {ex['assistant']}")

        return "\n".join(context_lines)

    def save_session(self, output_path: str):
        """Save conversation session to file"""
        session_data = {
            'participant': self.participant,
            'session_start': self.session_start.isoformat(),
            'session_end': datetime.now().isoformat(),
            'exchanges': self.exchanges
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Session saved to {output_path}")


class VoiceInterface:
    """Main voice interface orchestrator"""

    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()
        self.stt = WhisperSTT(self.config)
        self.tts = PiperTTS(self.config)
        self.recorder = AudioRecorder(self.config)
        self.memory = ConversationMemory(self.config.CONTEXT_MEMORY_SIZE)

        logger.info("Voice Interface initialized")

    def initialize(self):
        """Initialize models"""
        logger.info("Loading models...")
        self.stt.load_model()
        logger.info("Voice interface ready!")

    def listen(self) -> str:
        """
        Listen for voice input and transcribe

        Returns:
            Transcribed text
        """
        # Record audio
        audio_data = self.recorder.record_until_silence()

        # Transcribe
        result = self.stt.transcribe_numpy(audio_data)

        return result['text']

    def speak(self, text: str):
        """
        Speak text aloud

        Args:
            text: Text to speak
        """
        self.tts.speak(text)

    def conversation_turn(self, llm_callback) -> bool:
        """
        Execute one turn of conversation

        Args:
            llm_callback: Function that takes user text and returns assistant response

        Returns:
            True if conversation should continue, False to end
        """
        try:
            # Listen for user input
            logger.info("Listening...")
            user_text = self.listen()

            if not user_text.strip():
                logger.warning("No speech detected")
                return True

            logger.info(f"User said: {user_text}")

            # Check for exit phrases
            exit_phrases = ['beenden', 'stop', 'tschüss', 'auf wiedersehen', 'exit', 'quit']
            if any(phrase in user_text.lower() for phrase in exit_phrases):
                self.speak("Bis bald!")
                return False

            # Get LLM response with context
            context = self.memory.get_context()
            assistant_text = llm_callback(user_text, context)

            logger.info(f"Assistant: {assistant_text}")

            # Remember exchange
            self.memory.add_exchange(user_text, assistant_text)

            # Speak response
            self.speak(assistant_text)

            return True

        except KeyboardInterrupt:
            logger.info("Conversation interrupted by user")
            return False
        except Exception as e:
            logger.error(f"Conversation turn error: {e}")
            return True

    def run_conversation(self, llm_callback, greeting: Optional[str] = None):
        """
        Run full conversation loop

        Args:
            llm_callback: Function to get LLM responses
            greeting: Optional greeting message
        """
        try:
            # Greeting
            if greeting:
                self.speak(greeting)

            # Conversation loop
            while True:
                should_continue = self.conversation_turn(llm_callback)
                if not should_continue:
                    break

        except Exception as e:
            logger.error(f"Conversation error: {e}")
            raise
        finally:
            # Save session
            session_file = f"/data/conversations/session_{int(time.time())}.json"
            os.makedirs("/data/conversations", exist_ok=True)
            self.memory.save_session(session_file)


def demo_llm_callback(user_text: str, context: str) -> str:
    """Demo LLM callback for testing"""
    return f"Ich habe verstanden: {user_text}. Das ist nur ein Test."


def main():
    """Main entry point for testing"""
    import argparse

    parser = argparse.ArgumentParser(description="Kirobi Voice Interface")
    parser.add_argument('--test-stt', action='store_true', help='Test speech-to-text')
    parser.add_argument('--test-tts', type=str, help='Test text-to-speech with given text')
    parser.add_argument('--conversation', action='store_true', help='Run full conversation')

    args = parser.parse_args()

    config = VoiceConfig()
    voice = VoiceInterface(config)
    voice.initialize()

    if args.test_stt:
        print("Testing STT - speak now...")
        text = voice.listen()
        print(f"Transcribed: {text}")

    elif args.test_tts:
        print(f"Testing TTS: {args.test_tts}")
        voice.speak(args.test_tts)

    elif args.conversation:
        print("Starting conversation...")
        greeting = "Hallo! Ich bin Kirobi. Wie kann ich dir helfen?"
        voice.run_conversation(demo_llm_callback, greeting)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
