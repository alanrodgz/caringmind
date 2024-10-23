# File: route/post/gemini.py
# **DO NOT OMIT ANYTHING FROM THE FOLLOWING CONTENT, INCLUDING & NOT LIMITED TO COMMENTED NOTES

from fastapi import APIRouter, HTTPException, Form
from typing import Optional
import google.generativeai as genai
import os
import json

from dotenv import load_dotenv
from route.post.gemini_flash_series.gemini_series_config import MODEL_VARIANTS, SUPPORTED_LANGUAGES, SUPPORTED_RESPONSE_MIME_TYPES

# ------------------ Load Environment Variables --------------------
load_dotenv()

# ------------------ Initialize Router ------------------------------
router = APIRouter(
    tags=["Gemini Models"],
    # No prefix here
    responses={401: {"description": "Unauthorized"}}
)

# ------------------ Configure the GenAI Client ----------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is not set in the environment variables.")
genai.configure(api_key=GOOGLE_API_KEY)

# ------------------ Utility Functions -------------------------------
# Removed: save_upload_file function
# Removed: upload_to_genai function
# Removed: get_mime_type function

# ------------------ API Endpoints -------------------------------------

@router.post("/generate", summary="Generate Content")
async def generate_content(
    model: str = Form(..., description="Model variant to use", example="gemini-1.5-flash-8b"),
    text: Optional[str] = Form(None, description="Input text prompt"),
    language: Optional[str] = Form("en", description="Language code", example="en"),
    candidate_count: int = Form(1, description="Number of candidate responses", ge=1, le=5),
    max_output_tokens: int = Form(500, description="Maximum number of tokens in the output", ge=1, le=8192),
    temperature: float = Form(0.95, description="Sampling temperature", ge=0.0, le=2.0),
    top_p: float = Form(0.9, description="Nucleus sampling parameter", ge=0.0, le=1.0),
    response_mime_type: str = Form("application/json", description="Response MIME type", example="application/json"),
    stream: bool = Form(False, description="Stream the response")
    # Removed: send_files, audio_files, image_files, video_files parameters
):
    """
    Generate content using Gemini models. Supports text input.
    """
    if model not in MODEL_VARIANTS:
        raise HTTPException(status_code=400, detail=f"Unsupported model variant. Supported models: {list(MODEL_VARIANTS.keys())}")

    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language. Supported languages: {SUPPORTED_LANGUAGES}")

    if response_mime_type not in SUPPORTED_RESPONSE_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported response MIME type. Supported types: {SUPPORTED_RESPONSE_MIME_TYPES}")

    # Prepare contents
    contents = []
    if text:
        contents.append({
            "role": "user",
            "parts": [{"text": text}]
        })

    # Removed: Handling of file uploads

    # Generation configuration
    generation_config = {
        "temperature": temperature,
        "top_p": top_p,
        "max_output_tokens": max_output_tokens,
        "candidate_count": candidate_count,
        "response_mime_type": response_mime_type
    }

    # Safety settings (empty for this example, customize as needed)
    safety_settings = {}

    try:
        # Initialize the generative model
        gemini_model = genai.GenerativeModel(model_name=model)

        # Call the model to generate content
        response = gemini_model.generate_content(
            contents=contents,
            generation_config=generation_config,
            safety_settings=safety_settings,
            stream=stream
        )

        # Prepare the response
        if candidate_count == 1:
            return {"response": response.text}
        else:
            return {"responses": [candidate.text for candidate in response.candidates]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

@router.post("/chat", summary="Chat Session")
async def chat_session(
    model: str = Form(..., description="Model variant to use", example="gemini-1.5-flash-8b"),
    messages: str = Form(..., description="Conversation history in JSON format"),
    temperature: float = Form(0.95, description="Sampling temperature", ge=0.0, le=2.0),
    top_p: float = Form(0.9, description="Nucleus sampling parameter", ge=0.0, le=1.0)
):
    """
    Create or continue a chat session with the Gemini model.
    """
    if model not in MODEL_VARIANTS:
        raise HTTPException(status_code=400, detail=f"Unsupported model variant. Supported models: {list(MODEL_VARIANTS.keys())}")

    try:
        conversation = json.loads(messages)
        if not isinstance(conversation, list):
            raise ValueError("Messages must be a list of message objects.")

        # Determine whose turn it is
        model_turn = conversation[-1].get("role", "").lower() == "user"

        # Initialize the generative model
        gemini_model = genai.GenerativeModel(model_name=model)

        if model_turn:
            # User was last, send the last message
            chat = gemini_model.start_chat(history=conversation[:-1])
            last_message = conversation[-1]["parts"][0].get("text", "")
            response = chat.send_message(last_message)
        else:
            # Model was last, continue the conversation
            chat = gemini_model.start_chat(history=conversation)
            response = chat.send_message("")

        return {"response": response.text}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for messages.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat session failed: {e}")

# Removed: /upload endpoint

@router.get("/models", summary="List Models")
async def list_models():
    """
    List all available Gemini model variants.
    """
    return {"models": MODEL_VARIANTS}

@router.get("/languages", summary="List Supported Languages")
async def list_languages():
    """
    List all supported languages.
    """
    return {"languages": SUPPORTED_LANGUAGES}