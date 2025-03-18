import os
import time
from moviepy.editor import VideoFileClip
import google.generativeai as genai
import tempfile
from app.core.logging import logger
from datetime import datetime
from app.core.config import settings
from app.core.task_tracker import task_tracker
from pydub import AudioSegment
from typing import Tuple, List, Optional
import math
import re
import json
import asyncio

# Configure Google Gemini API
GENAI_API_KEY = settings.GEMINI_API_KEY
genai.configure(api_key=GENAI_API_KEY)

OUTPUT_FOLDER = os.path.abspath("video_analysis_output")
MAX_CHUNK_SIZE = 24 * 1024 * 1024  # 24MB limit
CHUNK_DURATION = 10 * 60 * 1000  # 10 minutes in milliseconds

# NSFW content detection patterns
NSFW_PATTERNS = [
    r'\b(?:sex|porn|xxx|adult|nude|naked|explicit|nsfw)\b',
    r'\b(?:masturbat(?:e|ion)|orgasm|erotic)\b',
    r'\b(?:breast|boob|tit|ass|penis|vagina|dick|cock|pussy)\b',
    r'\b(?:fuck|shit|bitch|cunt|whore|slut)\b',
    r'\b(?:strip(?:ping|per)|escort|prostitut(?:e|ion))\b',
    r'\b(?:hentai|rule34|onlyfans)\b'
]

'''
async def process_audio(video_content: bytes, task_id: str = None) -> Tuple[List[dict], Optional[str]]:
    """
    Process audio from video content, handling large files by splitting into chunks.
    """
    temp_video_file = None
    temp_audio_file = None
    output_folder = "video_analysis_output"

    try:
        # Create output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            logger.info(f"Output folder created/confirmed: {os.path.abspath(output_folder)}")

        # Save video content to temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            print("---------- reading file ----")
            temp_file.write(video_content)
            temp_video_file = temp_file.name
        logger.info(f"Temporary video file created at: {temp_video_file}")

        if task_id:
            task_tracker.update_progress(task_id, "Video file saved", 10)

        # Load video and extract audio
        video = AudioSegment.from_file(temp_video_file)
        if task_id:
            task_tracker.update_progress(task_id, "Video loaded for audio extraction", 15)

        # Save extracted audio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_filename = os.path.join(output_folder, f"extracted_audio_{timestamp}.wav")
        video.export(audio_filename, format="wav")
        logger.info(f"Saved extracted audio locally: {audio_filename}")

        if task_id:
            task_tracker.update_progress(task_id, "Audio extracted and saved", 25)

        # Get file info
        file_size = os.path.getsize(audio_filename)
        logger.info(f"Audio file size: {file_size} bytes")

        # Process audio in chunks if necessary
        if task_id:
            task_tracker.update_progress(task_id, "Starting audio transcription", 30)

        logger.info("Transcribing audio using Gemini Pro...")

        # Calculate number of chunks needed
        audio_length = len(video)
        num_chunks = math.ceil(audio_length / CHUNK_DURATION)
        logger.info(f"Audio length: {audio_length}ms, splitting into {num_chunks} chunks")

        # Process audio in chunks
        transcriptions = []
        chunk_files = []

        try:
            for i in range(num_chunks):
                start_time = i * CHUNK_DURATION
                end_time = min((i + 1) * CHUNK_DURATION, audio_length)

                # Extract chunk
                chunk = video[start_time:end_time]

                # Save chunk to temporary file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_chunk:
                    chunk.export(temp_chunk.name, format="wav")
                    chunk_files.append(temp_chunk.name)

                    # Check chunk size
                    chunk_size = os.path.getsize(temp_chunk.name)
                    logger.info(f"Chunk {i + 1}/{num_chunks} size: {chunk_size} bytes")

                    if chunk_size > MAX_CHUNK_SIZE:
                        raise ValueError(
                            f"Chunk {i + 1} size ({chunk_size} bytes) exceeds maximum allowed size ({MAX_CHUNK_SIZE} bytes)")

                    # Transcribe chunk
                    with open(temp_chunk.name, "rb") as audio_file:
                        response = genai.GenerativeModel("gemini-pro").generate_content(
                            ["Transcribe the following audio:", audio_file])
                        if hasattr(response, 'text'):
                            transcriptions.append({"text": response.text.strip()})
                        else:
                            transcriptions.append({"text": "No valid transcription received."})

                    logger.info(f"Chunk {i + 1}/{num_chunks} transcribed successfully")

                    if task_id:
                        progress = 30 + (i + 1) * (35 - 30) / num_chunks
                        task_tracker.update_progress(task_id, f"Transcribed chunk {i + 1}/{num_chunks}", progress)

            # Combine all transcriptions
            combined_text = " ".join(transcriptions)
            result = [{"text": combined_text}]

            if task_id:
                task_tracker.update_progress(task_id, "Audio transcription completed", 35)
                task_tracker.update_progress(task_id, "Audio processing completed", 40)

            return result, audio_filename

        finally:
            # Clean up chunk files
            for chunk_file in chunk_files:
                if os.path.exists(chunk_file):
                    try:
                        os.unlink(chunk_file)
                        logger.info(f"Cleaned up chunk file: {chunk_file}")
                    except Exception as e:
                        logger.error(f"Error cleaning up chunk file: {str(e)}")

    except Exception as e:
        error_msg = f"Error in audio processing: {str(e)}"
        logger.error(error_msg)
        if task_id:
            task_tracker.update_progress(task_id, f"Error: {error_msg}", 35)
        return [{"error": error_msg}], None

    finally:
        # Clean up temporary files
        if temp_video_file and os.path.exists(temp_video_file):
            try:
                os.unlink(temp_video_file)
                logger.info(f"Cleaned up temporary video file: {temp_video_file}")
            except Exception as e:
                logger.error(f"Error cleaning up temporary video file: {str(e)}")
'''
import os
import tempfile
import math
import datetime
import google.generativeai as genai
from pydub import AudioSegment
from pydub.utils import which
from typing import List, Tuple, Optional

# Ensure ffmpeg is found
AudioSegment.converter = which("ffmpeg")
AudioSegment.ffprobe = which("ffprobe")

# Define chunk size
CHUNK_DURATION: int = 30 * 1000  # 30 seconds per chunk

async def process_audio(video_content: bytes, task_id: str = None) -> Tuple[List[dict], Optional[str]]:
    temp_video_file = None
    chunk_files = []

    try:
        # Save video to temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_file.write(video_content)
            temp_video_file = temp_file.name

        # Extract audio
        video = AudioSegment.from_file(temp_video_file)

        # Split audio into chunks
        audio_length = len(video)
        num_chunks = math.ceil(audio_length / CHUNK_DURATION)

        transcriptions = []

        for i in range(num_chunks):
            start_time = i * CHUNK_DURATION
            end_time = min((i + 1) * CHUNK_DURATION, audio_length)

            chunk = video[start_time:end_time]

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_chunk:
                chunk.export(temp_chunk.name, format="wav")
                chunk_files.append(temp_chunk.name)

                with open(temp_chunk.name, "rb") as audio_file:
                    audio_bytes = audio_file.read()

                # Gemini Transcription
                model = genai.GenerativeModel("gemini-1.5-pro")
                response = model.generate_content([
                    "Transcribe the following audio:",
                    {"mime_type": "audio/wav", "data": audio_bytes}
                ])

                if hasattr(response, 'text'):
                    transcriptions.append({"text": response.text.strip()})

        # Combine transcriptions
        print("audio transcription Ekta",transcriptions)
        return [{"text": " ".join(t["text"] for t in transcriptions)}], temp_video_file

    except Exception as e:
        return [{"error": str(e)}], None

    finally:
        # Cleanup temp files
        if temp_video_file and os.path.exists(temp_video_file):
            os.unlink(temp_video_file)
        for chunk_file in chunk_files:
            if os.path.exists(chunk_file):
                os.unlink(chunk_file)

async def check_content_safety(text: str) -> Tuple[bool, List[str]]:
    """
    Check if the content is safe using Google Gemini.
    """
    try:
        warnings = [match.group() for pattern in NSFW_PATTERNS for match in re.finditer(pattern, text.lower())]
        if warnings:
            return False, warnings
        
        response = genai.GenerativeModel("gemini-pro").generate_content([
            "Does this text contain NSFW content? Reply with Yes or No.", text
        ])
        
        if "Yes" in response.text:
            return False, ["NSFW content detected."]
        return True, []
    
    except Exception as e:
        logger.error(f"Error in content safety check: {str(e)}")
        return False, ["Error in content safety check"]

