from io import BytesIO
from fastapi import APIRouter, Body, UploadFile, File, BackgroundTasks, Header
from app.services.video_processor import process_video
from app.services.audio_processor import process_audio
from app.services.keyword_extractor import extract_video_metadata
from app.core.logging import logger
from fastapi.param_functions import Query
from app.core.config import settings
from app.core.task_tracker import task_tracker
from typing import Optional
import uuid
import asyncio
import requests
import os
import time
import json
import google.generativeai as genai

# Configure Google Gemini API
GENAI_API_KEY = settings.GEMINI_API_KEY
genai.configure(api_key=GENAI_API_KEY)

MAX_RETRIES = 3
RETRY_DELAY = 10

EMPOWERVERSE_API_KEY = settings.EMPOWERVERSE_API_KEY
WEMOTIONS_API_KEY = settings.WEMOTIONS_API_KEY
EMPOWERVERSE_API_PATH = settings.EMPOWERVERSE_API_PATH
WEMOTIONS_API_PATH = settings.WEMOTIONS_API_PATH
VIDEO_DESCRIPTION_KEY = settings.VIDEO_DESCRIPTION_KEY

router = APIRouter()

analysis_results = {}

'''
async def analyze_video_task(video_content: bytes, video_filename: str, task_id: str, app_name: str,
                             identifier: Optional[str] = None, is_christian_content: Optional[bool] = False):
    """
    Process the video and generate metadata.
    """
    try:
        task_tracker.start_task(task_id)

        video_task = asyncio.create_task(process_video(video_content, task_id))
        audio_task = asyncio.create_task(process_audio(video_content, task_id))

        video_result, audio_result = await asyncio.gather(video_task, audio_task)

        is_safe, content_warnings, base64_grids = video_result
        audio_transcription = audio_result[0].get("text", "") if isinstance(audio_result, list) and audio_result else ""

        description = await generate_description(base64_grids, audio_transcription, task_id)
        metadata = await extract_video_metadata(description, is_christian_content, task_id)

        result = {
            "status": "completed",
            "description": description,
            "is_safe": is_safe,
            "content_warnings": content_warnings,
            "keywords": metadata.get("keywords", []),
            "is_face_exist": metadata.get("is_face_exist", False)
        }

        analysis_results[task_id] = result
        task_tracker.complete_task(task_id)

    except Exception as e:
        logger.error(f"Error in video processing: {str(e)}")
        analysis_results[task_id] = {"status": "error", "message": str(e)}

async def analyze_video_task(video_content: bytes, video_filename: str, task_id: str, app_name: str,
                             identifier: Optional[str] = None, is_christian_content: Optional[bool] = False):
    """
    Process the video and generate metadata.
    """
    try:
        task_tracker.start_task(task_id)

        # Run video and audio processing concurrently
        video_task = asyncio.create_task(process_video(video_content, task_id))
        audio_task = asyncio.create_task(process_audio(video_content, task_id))

        video_result, audio_result = await asyncio.gather(video_task, audio_task)

        # Extract values safely
        is_safe, content_warnings, base64_grids = video_result

        if isinstance(audio_result, list) and audio_result and isinstance(audio_result[0], dict):
            audio_transcription = audio_result[0].get("text", "")
        else:
            audio_transcription = ""

        # Limit transcription length to prevent token overflow
        MAX_TRANSCRIPT_LENGTH = 5000
        trimmed_transcription = audio_transcription[:MAX_TRANSCRIPT_LENGTH]

        # Generate description & metadata
        description = await generate_description(base64_grids, trimmed_transcription, task_id)
        metadata = await extract_video_metadata(description, is_christian_content, task_id)

        result = {
            "status": "completed",
            "description": description,
            "is_safe": is_safe,
            "content_warnings": content_warnings,
            "keywords": metadata.get("keywords", []),
            "is_face_exist": metadata.get("is_face_exist", False)
        }

        analysis_results[task_id] = result
        task_tracker.complete_task(task_id)

        return result  # Ensure the function returns the result

    except Exception as e:
        logger.error(f"Error in video processing: {str(e)}")
        analysis_results[task_id] = {"status": "error", "message": str(e)}
        return analysis_results[task_id]  # Return the error response 
'''
async def analyze_video_task(video_content: bytes, video_filename: str, task_id: str, app_name: str,
                             identifier: Optional[str] = None, is_christian_content: Optional[bool] = False):
    """
    Process the video and generate metadata.
    """
    try:
        task_tracker.start_task(task_id)

        # Run video and audio processing concurrently
        video_task = asyncio.create_task(process_video(video_content, task_id))
        audio_task = asyncio.create_task(process_audio(video_content, task_id))

        video_result, audio_result = await asyncio.gather(video_task, audio_task)
        logger.info(f"Audio result Krishan: {audio_result}")  # Debug print

        # Extract video processing results safely
        is_safe, content_warnings, base64_grids = video_result

        #if isinstance(audio_result, list) and audio_result and isinstance(audio_result[0], dict):
        #    audio_transcription = audio_result[0].get("text", "")
        #else:
        #    audio_transcription = "empty"

        # ✅ Ensure audio_result is a tuple and extract the first element
        if isinstance(audio_result, tuple) and len(audio_result) > 0:
            audio_data = audio_result[0]  # Extract first item (expected to be a list)

            if isinstance(audio_data, list) and audio_data:
                first_item = audio_data[0]
                if isinstance(first_item, dict) and "text" in first_item:
                    audio_transcription = first_item["text"]
                else:
                    logger.error(f"Unexpected audio result format: {first_item}")
                    audio_transcription = "empty"
            else:
                logger.error(f"Invalid audio data: {audio_data}")
                audio_transcription = "empty"
        else:
            logger.error(f"Invalid audio result: {audio_result}")
            audio_transcription = "empty"

        # Limit transcript length
        MAX_TRANSCRIPT_LENGTH = 5000
        trimmed_transcription = audio_transcription[:MAX_TRANSCRIPT_LENGTH]

        # Limit the number of images
        MAX_IMAGES = 3
        selected_images = base64_grids[:MAX_IMAGES]

        # Summarize long transcripts before passing
        print("Summarised Transcription:",trimmed_transcription)
        summary = await summarize_text(trimmed_transcription)
        print("Summary" ,summary)
        # Generate description with optimized input size
        description = await generate_description(selected_images, summary, task_id)
        print("")
        metadata = await extract_video_metadata(description, is_christian_content, task_id)

        result = {
            "status": "completed",
            "description": description,
            "is_safe": is_safe,
            "content_warnings": content_warnings,
            "keywords": metadata.get("keywords", []),
            "is_face_exist": metadata.get("is_face_exist", False)
        }

        analysis_results[task_id] = result
        task_tracker.complete_task(task_id)

        return result

    except Exception as e:
        logger.error(f"Error in video processing: {str(e)}")
        analysis_results[task_id] = {"status": "error", "message": str(e)}
        return analysis_results[task_id]

async def summarize_text(text: str) -> str:
    """
    Summarize long transcripts using Gemini API.
    """
    model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp")
    response = model.generate_content(f"Summarize this: {text[:9000]}", stream=False)
    return response.text if response else "Summary unavailable"
'''
async def generate_description(base64_grids: list, audio_transcription: str, task_id: str) -> str:
    """
    Generate video description using Google Gemini.
    """
    prompt = f"""
    Analyze the following video frames and transcribed audio. Generate a detailed description including:
    - Key subjects and objects in the scene
    - Actions happening in the frames
    - Overall mood or theme
    - Important spoken words from the audio transcription
    
    Video Frames: {base64_grids}
    Audio Transcript: {audio_transcription}
    """
    
    response = genai.GenerativeModel("gemini-2.0-flash-thinking-exp").generate_content(prompt)
    return response.text.strip() if hasattr(response, 'text') else "No valid description received."
'''
import google.generativeai as genai
import base64

import google.generativeai as genai
import base64

async def generate_description(base64_grids: list, audio_transcription: str, task_id: str) -> str:
    """
    Generate a video description using Google Gemini with correctly structured input.
    """
    try:
        # ✅ Limit number of images processed
        MAX_IMAGES = 3
        selected_images = base64_grids[:MAX_IMAGES]

        # ✅ Limit transcript length
        MAX_TRANSCRIPT_LENGTH = 2000
        trimmed_transcription = audio_transcription[:MAX_TRANSCRIPT_LENGTH]

        # ✅ Prepare the text prompt
        text_prompt = f"""
        Analyze the following video frames and transcribed audio. Generate a **detailed yet concise** description including:
        - Key subjects and objects in the scene
        - Actions happening in the frames
        - Overall mood or theme
        - Important spoken words from the audio transcript

        Audio Transcript (Trimmed): {trimmed_transcription}
        """

        # ✅ Format images correctly as input
        image_inputs = [
            {"inline_data": {"mime_type": "image/png", "data": img}} for img in selected_images
        ]

        # ✅ Use the correct Gemini model
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content({"parts": [{"text": text_prompt}] + image_inputs})

        # ✅ Extract and return response text
        return response.text.strip() if hasattr(response, "text") else "No valid description received."

    except Exception as e:
        logger.error(f"Error in generate_description: {str(e)}")
        return "Error generating description."





@router.post("/analyze_video")
async def analyze_video(background_tasks: BackgroundTasks, app_name: str="app_name", video: UploadFile = File(None), file_url: Optional[str] = Query(None), identifier: Optional[str] = Query(None), is_christian_content: Optional[bool] = Query(False)):
    """
    API endpoint to analyze a video file.
    """
    try:
        task_id = str(uuid.uuid4())
        if file_url:
            for attempt in range(MAX_RETRIES):
                response = requests.get(file_url)
                if response.status_code == 200:
                    response.raise_for_status()
                    file_content = response.content
                    filename = os.path.basename(file_url)

                    #progress_bar += 1
                    background_tasks.add_task(analyze_video_task, file_content, filename, task_id, app_name, identifier, is_christian_content)
                    break

                print(f"Attempt {attempt + 1}: Result not ready. Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
        elif video:
            video_content = await video.read()
            #progress_bar += 1
            background_tasks.add_task(analyze_video_task, video_content, video.filename, task_id, app_name, identifier, is_christian_content)
        return {"message": "Video analysis started.", "task_id": task_id}
    except requests.RequestException as e:
        logger.error(f"Error during video analysis: {str(e)}")
        return {"error": "Failed to process video"}

@router.get("/analysis_result/{task_id}")
async def get_analysis_result(task_id: str):
    """
    API endpoint to fetch analysis results for a given task ID.
    """
    result = analysis_results.get(task_id)
    if result is None:
        # Get progress from task tracker
        task_data = task_tracker.tasks.get(task_id)
        if task_data:
            return {
                "status": "pending",
                "progress": task_data["current_progress"],
                "current_step": list(task_data["steps"].keys())[-1] if task_data["steps"] else None
            }
        return {"status": "pending", "progress": 0}
    return result

@router.post("/share_url")
async def share_url(
    background_tasks: BackgroundTasks,
    flic_token: str = Header(...),
    data: dict = Body(...)
):
    """
    API endpoint to share a video URL for processing.
    """
    url = data.get('url')
    identifier = data.get('identifier')
    is_christian_content = data.get('is_christian_content', False)

    if flic_token == EMPOWERVERSE_API_KEY:
        app_name = "empowerverse"
    elif flic_token == WEMOTIONS_API_KEY:
        app_name = "wemotions"
    else:
        return {"status": "error", "message": "Invalid Flic_Token"}

    if not url or not identifier:
        return {"status": "error", "message": "url and identifier are required fields"}

    background_tasks.add_task(analyze_video, background_tasks, app_name, file_url=url, identifier=identifier, is_christian_content=is_christian_content)
    return {"status": "success", "message": "URL processed successfully, video processing in queue..."}



