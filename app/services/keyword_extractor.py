import google.generativeai as genai
from app.core import task_tracker
from app.core.config import settings
from app.core.logging import logger
import json
import google.generativeai as genai

# Configure Google Gemini API
GENAI_API_KEY = settings.GEMINI_API_KEY
genai.configure(api_key=GENAI_API_KEY)
'''
async def extract_video_metadata(description: str, is_christian_content: bool = False, task_id: str = None) -> dict:
    """
    Extract metadata from video description using GPT-4.
    
    Args:
        description (str): Video description
        is_christian_content (bool): Whether to analyze for Christian content
        task_id (str): Task identifier for progress tracking
        
    Returns:
        dict: Extracted metadata with all required fields
    """
    try:
        # Refined prompt for structured extraction
        prompt = f"""
        You are an expert content analyst. Analyze the following video description and extract metadata in the exact JSON structure provided below:
        
        Video Description:
        {description}

        Extracted Metadata:
        {{
            "description": "{description}",  // Original video description
            "keywords": [
                {{"keyword":"string","weight":int}}  // Extract 10 most relevant keywords with weights (1-10) and make sure atleast 5 keywords are present
            ],
            "topics": ["string"],  // List at least 3 key topics discussed
            "entities": ["string"],  // Mentioned people, organizations, or objects
            "actions": ["string"],  // Key actions described
            "emotions": ["string"],  // Emotional tones present
            "visual_elements": ["string"],  // Notable visual elements
            "audio_elements": ["string"],  // Sound elements mentioned
            "genre": "string",  // Genre of the content
            "target_audience": ["string"],  // List of intended audiences
            "duration_estimate": "string",  // Estimated duration in minutes:seconds
            "quality_indicators": ["string"],  // Quality metrics or indicators
            "unique_identifiers": ["string"],  // Unique identifiers for the video
            "is_face_exist": bool,  // Whether faces are present in the video
            "person_identity": {{"name": "string", "gender": "string"}},  // Main person identity
            "other_person_identity": ["string"],  // Other persons' identities
            "psychological_personality": ["string"],  // Personality traits
            "no_of_person_in_video": int,  // Number of persons in the video if no person found then attach no_of_person_in_video = 0
            "content_warnings": ["string"],  // List of content warnings
            "safety_analysis": ["string"],  // Safety-related observations
            "is_safe": bool  // Whether the content is deemed safe
        }}
        
        Ensure all fields are filled based on the information available in the description.
        Return the response in valid JSON format.
        """
        
        response = genai.GenerativeModel("gemini-2.0-flash-thinking-exp").generate_content(prompt)
        extracted_metadata = json.loads(response.text.strip()) if hasattr(response, 'text') else {}
        
        if is_christian_content:
            christian_content = await analyze_christian_content(description, task_id)
            extracted_metadata["is_christian_content"] = christian_content
        
        logger.info("Extracted metadata:")
        logger.info(json.dumps(extracted_metadata, indent=2))
        return extracted_metadata
    except Exception as e:
        logger.error(f"Error during metadata extraction: {str(e)}")
        return {}
Working json parsing error

async def extract_video_metadata(description: str, is_christian_content: bool = False, task_id: str = None) -> dict:
    """
    Extract metadata from video description using Google Gemini.
    """
    try:
        # ✅ Validate input: Ensure the description is provided
        if not description.strip():
            logger.error("Error: Description is empty. Cannot extract metadata.")
            return {}

        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
        You are an expert content analyst. Analyze the following video description and extract metadata in **valid JSON format**:

        ### Video Description:
        {description}

        ### Expected JSON Response:
        {{
            "description": "{description}",
            "keywords": [
                {{"keyword": "string", "weight": int}}
            ],
            "topics": ["string"],  
            "entities": ["string"],  
            "actions": ["string"],  
            "emotions": ["string"],  
            "visual_elements": ["string"],  
            "audio_elements": ["string"],  
            "genre": "string",  
            "target_audience": ["string"],  
            "duration_estimate": "string",  
            "quality_indicators": ["string"],  
            "unique_identifiers": ["string"],  
            "is_face_exist": bool,  
            "person_identity": {{"name": "string", "gender": "string"}},  
            "other_person_identity": ["string"],  
            "psychological_personality": ["string"],  
            "no_of_person_in_video": int,  
            "content_warnings": ["string"],  
            "safety_analysis": ["string"],  
            "is_safe": bool  
        }}

        **Ensure the response is strictly in JSON format. If the audio transcript is missing, still analyze the video description.**
        """

        # ✅ Generate response using Gemini
        response = model.generate_content({"parts": [{"text": prompt}]})

        # ✅ Extract and validate response
        response_text = response.text.strip() if hasattr(response, "text") else ""
        if not response_text:
            raise ValueError("Gemini returned an empty response.")

        # ✅ Check for placeholder responses
        # if "provide the audio transcript" in response_text.lower():
        #     logger.error("Gemini is expecting audio input. Sending only video description.")
        #     return {}
        print("---response_text---",response_text)
        # ✅ Convert response to JSON safely
        extracted_metadata = json.loads(response_text)

        if is_christian_content:
            christian_content = await analyze_christian_content(description, task_id)
            extracted_metadata["is_christian_content"] = christian_content

        logger.info("Extracted metadata:")
        logger.info(json.dumps(extracted_metadata, indent=2))
        return extracted_metadata

    except json.JSONDecodeError as e:
        logger.error(f"JSON Parsing Error: {str(e)}. Response: {response_text}")
    except Exception as e:
        logger.error(f"Error during metadata extraction: {str(e)}")

    return {}
'''
async def extract_video_metadata(description: str, is_christian_content: bool = False, task_id: str = None) -> dict:
    """
    Extract metadata from video description using Google Gemini.
    """
    try:
        # Validate input
        if not description.strip():
            logger.error("Error: Description is empty. Cannot extract metadata.")
            return {}

        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
        You are an expert AI in metadata extraction. Analyze the given **video description** and return metadata in **valid JSON format** ONLY.

        ### Video Description:
        {description}

        ### STRICT JSON Response Format:
        {{
            "description": "{description}",
            "keywords": [
                {{"keyword": "string", "weight": int}}
            ],
            "topics": ["string"],  
            "entities": ["string"],  
            "actions": ["string"],  
            "emotions": ["string"],  
            "visual_elements": ["string"],  
            "audio_elements": ["string"],  
            "genre": "string",  
            "target_audience": ["string"],  
            "duration_estimate": "string",  
            "quality_indicators": ["string"],  
            "unique_identifiers": ["string"],  
            "is_face_exist": bool,  
            "person_identity": {{"name": "string", "gender": "string"}},  
            "other_person_identity": ["string"],  
            "psychological_personality": ["string"],  
            "no_of_person_in_video": int,  
            "content_warnings": ["string"],  
            "safety_analysis": ["string"],  
            "is_safe": bool  
        }}

        **Important Rules:**  
        - Do NOT include explanations.  
        - Do NOT return Markdown formatting (` ```json `).  
        - Ensure ALL required fields are present.  
        - If data is missing, return an empty list `[]` or null where applicable.  
        - Response should be a valid JSON object.  
        """

        #  Generate response from Gemini
        response = model.generate_content({"parts": [{"text": prompt}]})

        # Ensure response is available
        response_text = response.text.strip() if hasattr(response, "text") else ""
        if not response_text:
            raise ValueError("Gemini returned an empty response.")

        if response_text.startswith("```json"):
            response_text = response_text.strip("```json").strip("```").strip()

        print("--- Gemini Raw Response ---")
        print(response_text)

        # Attempt to parse JSON
        extracted_metadata = json.loads(response_text)

        #  Handle Christian content analysis (if applicable)
        if is_christian_content:
            christian_content = await analyze_christian_content(description, task_id)
            extracted_metadata["is_christian_content"] = christian_content

        logger.info("Extracted metadata:")
        logger.info(json.dumps(extracted_metadata, indent=2))
        return extracted_metadata

    except json.JSONDecodeError as e:
        logger.error(f"JSON Parsing Error: {str(e)}. Response: {response_text}")
    except Exception as e:
        logger.error(f"Error during metadata extraction: {str(e)}")

    return {}

# async def extract_video_metadata(description: str, is_christian_content: bool = False, task_id: str = None) -> dict:
#     """
#     Extract metadata from video description using Google Gemini.
#     """
#     try:
#         #  Validate input: Ensure the description is provided
#         if not description.strip():
#             logger.error("Error: Description is empty. Cannot extract metadata.")
#             return {}
#
#         model = genai.GenerativeModel("gemini-1.5-flash")
#
#         prompt = f"""
#         You are an expert content analyst. Analyze the following video description and extract metadata in **valid JSON format**:
#
#         ### Video Description:
#         {description}
#
#         ### Expected JSON Response:
#         {{
#             "description": "{description}",
#             "keywords": [
#                 {{"keyword": "string", "weight": int}}
#             ],
#             "topics": ["string"],
#             "entities": ["string"],
#             "actions": ["string"],
#             "emotions": ["string"],
#             "visual_elements": ["string"],
#             "audio_elements": ["string"],
#             "genre": "string",
#             "target_audience": ["string"],
#             "duration_estimate": "string",
#             "quality_indicators": ["string"],
#             "unique_identifiers": ["string"],
#             "is_face_exist": bool,
#             "person_identity": {{"name": "string", "gender": "string"}},
#             "other_person_identity": ["string"],
#             "psychological_personality": ["string"],
#             "no_of_person_in_video": int,
#             "content_warnings": ["string"],
#             "safety_analysis": ["string"],
#             "is_safe": bool
#         }}
#
#         **Ensure the response is strictly in JSON format. If the audio transcript is missing, still analyze the video description.**
#         """
#
#         #  Generate response using Gemini
#         response = model.generate_content({"parts": [{"text": prompt}]})
#
#         # # start : added by me
#         # #  Log raw response to debug
#         # logger.debug(f"Raw response from Gemini: {response.text}")
#         print("---- response :")
#         # # end
#
#         #  Extract and validate response
#         response_text = response.text.strip() if hasattr(response, "text") else ""
#         if not response_text:
#             raise ValueError("Gemini returned an empty response.")
#
#         # Check for placeholder responses
#         if "provide the audio transcript" in response_text.lower():
#             logger.error("Gemini is expecting audio input. Sending only video description.")
#             return {}
#
#         print("---- response_text is ---",response_text)
#
#         #  Convert response to JSON safely
#         extracted_metadata = json.loads(response_text)
#         print("---- extracted_metadata is ---", extracted_metadata)
#
#         if is_christian_content:
#             christian_content = await analyze_christian_content(description, task_id)
#             extracted_metadata["is_christian_content"] = christian_content
#
#         logger.info("Extracted metadata:")
#         logger.info(json.dumps(extracted_metadata, indent=2))
#         return extracted_metadata
#
#     except json.JSONDecodeError as e:
#         logger.error(f"JSON Parsing Error: {str(e)}. Response: {response_text}")
#     except Exception as e:
#         logger.error(f"Error during metadata extraction: {str(e)}")
#
#     return {}  # Return an empty dict on failure

# # By Me
# async def extract_video_metadata(description: str, is_christian_content: bool = False, task_id: str = None) -> dict:
#     """
#     Extract metadata from video description using Google Gemini.
#     """
#     try:
#         #  Validate input: Ensure the description is provided
#         if not description.strip():
#             logger.error("Error: Description is empty. Cannot extract metadata.")
#             return {}
#
#         model = genai.GenerativeModel("gemini-1.5-flash")
#
#         prompt = f"""
#         You are an expert content analyst. Analyze the following video description and extract metadata in **valid JSON format**:
#
#         ### Video Description:
#         {description}
#
#         **Note**: There is no audio transcript available for analysis. Please proceed with analyzing the description only.
#
#         ### Expected JSON Response:
#         {{
#             "description": "{description}",
#             "keywords": [
#                 {{"keyword": "string", "weight": int}}
#             ],
#             "topics": ["string"],
#             "entities": ["string"],
#             "actions": ["string"],
#             "emotions": ["string"],
#             "visual_elements": ["string"],
#             "audio_elements": ["string"],
#             "genre": "string",
#             "target_audience": ["string"],
#             "duration_estimate": "string",
#             "quality_indicators": ["string"],
#             "unique_identifiers": ["string"],
#             "is_face_exist": bool,
#             "person_identity": {{"name": "string", "gender": "string"}},
#             "other_person_identity": ["string"],
#             "psychological_personality": ["string"],
#             "no_of_person_in_video": int,
#             "content_warnings": ["string"],
#             "safety_analysis": ["string"],
#             "is_safe": bool
#         }}
#
#         **Ensure the response is strictly in JSON format. If the audio transcript is missing, still analyze the video description.**
#         """
#
#         #  Generate response using Gemini
#         response = model.generate_content({"parts": [{"text": prompt}]})
#
#         #  Extract and validate response
#         response_text = response.text.strip() if hasattr(response, "text") else ""
#         print(" -- line 223--")
#         print("--- response_text -- is :",response_text)
#         if not response_text:
#             logger.error("Error: Gemini returned an empty response.")
#             return {}
#
#         print(" -- line 229--")
#         #  Check for placeholder responses like "audio transcript missing"
#         if "provide the audio transcript" in response_text.lower():
#             logger.error("Gemini is expecting audio input. Sending only video description.")
#             return {}
#
#         #  Check if the response is valid JSON by attempting to parse it
#         try:
#             extracted_metadata = json.loads(response_text)
#         except json.JSONDecodeError as e:
#             # Log the error with the response text to help debug
#             logger.error(f"JSON Parsing Error: {str(e)}. Response: {response_text}")
#             return {}
#
#         if is_christian_content:
#             christian_content = await analyze_christian_content(description, task_id)
#             extracted_metadata["is_christian_content"] = christian_content
#
#         logger.info("Extracted metadata:")
#         logger.info(json.dumps(extracted_metadata, indent=2))
#         return extracted_metadata
#
#     except Exception as e:
#         logger.error(f"Error during metadata extraction: {str(e)}")
#         return {}


async def analyze_christian_content(description: str, task_id: str = None) -> dict:
    """
    Analyze a video description to determine the presence of Christian content.

    Args:
        description (str): Video description to analyze.
        task_id (str): Task identifier for progress tracking (optional).

    Returns:
        dict: Analysis results with the following fields:
            - is_christian: Boolean indicating if Christian content is present.
            - confidence_score: Float (0.0 to 1.0) representing confidence level.
            - indicators: List of specific Christian elements/themes detected.
    """
    try:
        # ✅ Use the correct Gemini model
        model = genai.GenerativeModel("gemini-1.5-pro")

        prompt = f"""You are an expert in analyzing content for Christian themes.
        Based on the given description, identify if it contains Christian content.
        Provide the following details:
        - "is_christian": Boolean (true if Christian content is present, else false).
        - "confidence_score": Float (0.0-1.0) representing the certainty.
        - "indicators": List of specific Christian elements/themes (e.g., Bible verses, religious symbols, mentions of Jesus, etc.).

        Return the result **strictly in valid JSON format**.

        ### Video Description:
        {description}
        """

        #  Call Gemini model correctly
        response = model.generate_content(prompt)

        #  Extract JSON response safely
        response_text = response.text.strip() if hasattr(response, "text") else ""
        if not response_text:
            raise ValueError("Gemini returned an empty response.")

        #  Convert response to JSON safely
        result = json.loads(response_text)

        #  Ensure required fields exist
        result.setdefault("is_christian", False)
        result.setdefault("confidence_score", 0.0)
        result.setdefault("indicators", [])

        logger.info("Christian content analysis result:")
        logger.info(json.dumps(result, indent=2))
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {str(e)}. Response: {response_text}")
    except Exception as e:
        logger.error(f"Error in Christian content analysis: {str(e)}")

    return {
        "is_christian": False,
        "confidence_score": 0.0,
        "indicators": []
    }


