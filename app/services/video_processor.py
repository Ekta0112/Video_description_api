import cv2
import numpy as np
from PIL import Image
import io
import base64
import google.generativeai as genai
from app.core.logging import logger
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from app.core.config import settings
import asyncio
from collections import defaultdict
import tempfile
import os
from app.core.task_tracker import task_tracker
import json

# Task queue to store processing results
task_queue: Dict[str, Dict] = defaultdict(dict)

# Configure Google Gemini API
GENAI_API_KEY = settings.GEMINI_API_KEY
genai.configure(api_key=GENAI_API_KEY)

models = genai.list_models()
for model in models:
    print(model.name, "->", model.supported_generation_methods)

# Load the Gemini model
model = genai.GenerativeModel("gemini-2.0-flash-exp-image-generation")

'''async def split_video(video_content: bytes, task_id: str) -> List[bytes]:
    """
    Split video into chunks based on duration.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    temp_file.write(video_content)
    temp_file.close()
    
    cap = cv2.VideoCapture(temp_file.name)
    if not cap.isOpened():
        raise ValueError("Failed to open video file.")
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps > 0 else 0
    num_parts = min(5, max(1, int(duration / 60)))
    frames_per_part = total_frames // num_parts
    
    video_chunks = []
    for i in range(num_parts):
        start_frame = i * frames_per_part
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        ret, frame = cap.read()
        print("frame_kkkkkkk", frame)
        if ret:
            _, buffer = cv2.imencode(".jpg", frame)
            video_chunks.append(buffer.tobytes())
    cap.release()
    os.unlink(temp_file.name)
    return video_chunks'''
''''''

import os
import cv2
import tempfile
import numpy as np
from typing import List

import os
import cv2
import tempfile
import numpy as np
from typing import List


async def split_video(video_content: bytes, task_id: str) -> List[bytes]:
    """
    Splits video into smaller chunks while ensuring the output does not exceed API token limits.
    """

    # Create a temporary file safely
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        temp_file.write(video_content)
        temp_file_path = temp_file.name  # Save path before closing

    cap = cv2.VideoCapture(temp_file_path)
    if not cap.isOpened():
        os.unlink(temp_file_path)  # Ensure file is deleted if an error occurs
        raise ValueError("Failed to open video file.")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if fps == 0 or total_frames == 0:
        cap.release()
        os.unlink(temp_file_path)
        raise ValueError("Invalid FPS or empty video.")

    duration = total_frames / fps
    max_chunks = min(5, max(1, int(duration / 60)))  # Limit chunks to avoid exceeding token limit
    frames_per_part = total_frames // max_chunks

    video_chunks = []
    frame_skip = max(1, fps // 2)  # Process every other frame to reduce size

    for i in range(max_chunks):
        start_frame = i * frames_per_part
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as chunk_temp:
            chunk_temp_path = chunk_temp.name  # Store path before closing

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(chunk_temp_path, fourcc, fps, (width, height))

        frame_count = 0
        while frame_count < frames_per_part:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % frame_skip == 0:  # Skip frames to reduce size
                out.write(frame)
            frame_count += 1

        out.release()  # Close the VideoWriter before deleting

        with open(chunk_temp_path, "rb") as f:
            video_chunks.append(f.read())

        os.unlink(chunk_temp_path)  # Delete chunk file after reading

    cap.release()
    os.unlink(temp_file_path)  # Ensure the main temp file is deleted

    return video_chunks

async def extract_frames(video_chunk: bytes) -> str:
    """
    Extract frames and return a base64-encoded grid.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    temp_file.write(video_chunk)
    temp_file.close()
    
    cap = cv2.VideoCapture(temp_file.name)
    if not cap.isOpened():
        raise ValueError("Failed to open video chunk.")
    
    frames = []
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    interval = max(1, total_frames // 16)
    for i in range(16):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i * interval)
        ret, frame = cap.read()
        if ret:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    os.unlink(temp_file.name)
    
    if not frames:
        return None
    
    grid = Image.new('RGB', (frames[0].shape[1] * 4, frames[0].shape[0] * 4))
    for i, frame in enumerate(frames):
        img = Image.fromarray(frame)
        grid.paste(img, ((i % 4) * frames[0].shape[1], (i // 4) * frames[0].shape[0]))
    
    buffer = io.BytesIO()
    grid.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

async def analyze_grid_images(base64_images: List[str], task_id: str = None) -> List[str]:
    """
    Analyze grid images using Google Gemini.
    """
    descriptions = []
    for base64_image in base64_images:
        image_data = base64.b64decode(base64_image)
        response = model.generate_content([
            "Describe the key visual elements, actions, and scene composition in this frame grid.",
            {"mime_type": "image/png", "data": image_data}
        ])
        description = response.text.strip() if hasattr(response, 'text') else "No valid response."
        descriptions.append(description)
    return descriptions

async def check_content_moderation(base64_images: List[str]) -> Tuple[bool, List[str]]:
    """
    Use Gemini for NSFW content moderation.
    """
    flagged_warnings = []
    is_safe = True
    for base64_image in base64_images:
        image_data = base64.b64decode(base64_image)
        response = model.generate_content([
            "Does this image contain NSFW content (nudity, violence, hate speech)? Reply with Yes or No.",
            {"mime_type": "image/png", "data": image_data}
        ])
        if "Yes" in response.text:
            is_safe = False
            flagged_warnings.append("NSFW content detected.")
    return is_safe, flagged_warnings

async def process_video(video_content: bytes, task_id: str) -> Tuple[bool, List[str], List[str]]:
    """
    Process video by splitting, extracting frames, and analyzing.
    """
    video_chunks = await split_video(video_content, task_id)
    base64_grids = await asyncio.gather(*[extract_frames(chunk) for chunk in video_chunks])
    valid_grids = [grid for grid in base64_grids if grid is not None]
    is_safe, warnings = await check_content_moderation(valid_grids)
    return is_safe, warnings, valid_grids

