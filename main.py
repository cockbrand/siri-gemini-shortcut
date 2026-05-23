import os
import logging
from flask import Response, stream_with_context, request, jsonify
from google import genai
from google.genai import types

# --- CONFIGURATION ---
# The model ID is now centralized here for easy updates.
MODEL_ID = "gemini-3.1-flash-lite" 
API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize client globally for better performance in serverless environments
client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(api_version='v1beta')
) if API_KEY else None

def siri_gemini(request):
    """
    Flask entry point for the Siri-Gemini integration.
    Handles user queries with location context and streams the response.
    """
    if not client:
        logging.error("GEMINI_API_KEY is not configured.")
        return jsonify({"error": "Server configuration error."}), 500

    # Parse request data
    request_json = request.get_json(silent=True) or {}
    user_query = request_json.get('query')
    lat = request_json.get('lat')
    lon = request_json.get('lon')

    if not user_query:
        return jsonify({"error": "Missing 'query' in request body."}), 400

    # Prepare location context
    raw_location = f"User coordinates: {lat}, {lon}." if lat and lon else "Location unknown."

    system_prompt = (
        "You are a concise voice assistant for Siri. Follow these strict rules:\n"
        "1. VERBOSITY: Always give the shortest possible helpful answer (1-2 sentences). "
        "Only provide long explanations if the user explicitly asks to 'explain in detail' or 'be verbose'.\n"
        "2. LOCATION: You are provided with the user's location for context: {location}. "
        "DO NOT mention the location, coordinates, or local facts UNLESS the query is specifically about the user's "
        "current surroundings (e.g., weather, nearby places, local time).\n"
        "3. FORMATTING: Use metric units. Ensure the response is optimized for Text-to-Speech (no markdown, no complex symbols).\n"
        "4. ASSUMPTIONS: Assume the user is male unless context suggests otherwise."
    ).format(location=raw_location)

    def generate():
        try:
            # Use the global MODEL_ID variable here
            response_stream = client.models.generate_content_stream(
                model=MODEL_ID,
                contents=user_query,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    # Note: thinking_config availability depends on the specific model used
                    thinking_config=types.ThinkingConfig(
                        thinking_level=types.ThinkingLevel.LOW 
                    ) if "thinking" in MODEL_ID.lower() else None
                )
            )
            
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logging.error(f"Streaming error with model {MODEL_ID}: {e}")
            yield f"I'm sorry, I encountered an error: {str(e)}"

    return Response(stream_with_context(generate()), mimetype='text/plain')
