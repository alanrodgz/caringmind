# backend/route/post/geminiflash/gemini_socket.py
# File: backend/route/post/geminiflash/gemini_socket.py
# **DO NOT OMIT ANYTHING FROM THE FOLLOWING CONTENT, INCLUDING & NOT LIMITED TO COMMENTED NOTES

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
import google.generativeai as genai
import json
import os
import logging

from route.post.gemini_flash_series.gemini_series_config import MODEL_VARIANTS, SUPPORTED_RESPONSE_MIME_TYPES

router = APIRouter()

# Ensure that your API key is loaded from the environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is not set in the environment variables.")
genai.configure(api_key=GOOGLE_API_KEY)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time Gemini chat sessions.
    """
    await websocket.accept()
    conversation_history = []  # To maintain conversation context per connection

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)

                # Check if it's a text message
                if message.get("type") == "text":
                    # Handle text message
                    role = message.get("role")
                    text = message.get("text")
                    model_name = message.get("model_name", "gemini-1.5-flash-8b")  # Default model
                    generation_config = message.get("generation_config", {
                        "temperature": 0.95,
                        "top_p": 0.9,
                        "max_output_tokens": 8192,
                        "candidate_count": 1,
                        "response_mime_type": "text/plain"
                    })
                    stream = message.get("stream", False)

                    if role != "user" or not text:
                        await websocket.send_text(json.dumps({"error": "Invalid message format. Expected 'role': 'user' and 'text': 'your message'."}))
                        continue

                    # Append user's text message to conversation history
                    conversation_history.append({
                        "role": "user",
                        "parts": [{"text": text}]
                    })

                else:
                    # Removed: Handling of audio messages
                    await websocket.send_text(json.dumps({"error": "Unsupported message type."}))
                    continue

                # Log the conversation history for debugging
                logger.info(f"Conversation History: {json.dumps(conversation_history, indent=2)}")

    # TODO: THIS should all be included in the client request

    # --------------------
                # Validate model_name
                if model_name not in MODEL_VARIANTS:
                    await websocket.send_text(json.dumps({"error": f"Unsupported model variant. Supported models: {list(MODEL_VARIANTS.keys())}"}))
                    continue

                # Validate generation_config
                response_mime_type = generation_config.get("response_mime_type", "text/plain")
                if response_mime_type not in SUPPORTED_RESPONSE_MIME_TYPES:
                    await websocket.send_text(json.dumps({"error": f"Unsupported response MIME type. Supported types: {SUPPORTED_RESPONSE_MIME_TYPES}"}))
                    continue

                # Call the Gemini model to generate a response
                gemini_model = genai.GenerativeModel(model_name=model_name)

                # Call the model to generate content
                response = gemini_model.generate_content(
                    contents=conversation_history,
                    generation_config=generation_config,
                    safety_settings={},
                    stream=stream
                )
    # -------------------------

                # Parse the response to handle double serialization issue
                try:
                    response_content = json.loads(response.text)
                    if "text" in response_content:
                        model_response_text = response_content["text"]
                    else:
                        model_response_text = response.text  # Fallback if no 'text' field
                except json.JSONDecodeError:
                    model_response_text = response.text  # Handle the case where it's not JSON

                # Append model's response to history with the role "model"
                conversation_history.append({
                    "role": "model",
                    "parts": [{"text": model_response_text}]
                })

                # Log the updated conversation history
                logger.info(f"Updated Conversation History: {json.dumps(conversation_history, indent=2)}")

                # Send the response back to the client
                await websocket.send_text(json.dumps({"response": model_response_text}))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON format."}))
            except Exception as e:
                logger.error(f"Chat failed: {str(e)}", exc_info=True)
                await websocket.send_text(json.dumps({"error": f"Chat failed: {str(e)}"}))

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed.")

# cd /Users/ebowwa/irl/backend/route/post/geminiflash
# python3 -m http.server 8000

# python '/Users/ebowwa/irl/backend/index.py'