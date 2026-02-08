import os
import logging
from flask import Response, stream_with_context, request, jsonify
from google import genai
from google.genai import types

# Initialize client globally for better Cloud Run performance
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(api_version='v1beta')
) if api_key else None

def siri_gemini(request):
    if not client:
        return jsonify({"error": "GEMINI_API_KEY not set."}), 500

    request_json = request.get_json(silent=True)
    user_query = request_json.get('query') if request_json else None
    lat = request_json.get('lat')
    lon = request_json.get('lon')

    if not user_query:
        return jsonify({"error": "Missing 'query' in request body."}), 400

    # Pass location datan and instruct the model to ignore it unless necessary
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
            response_stream = client.models.generate_content_stream(
                model='gemini-3-flash-preview',
                contents=user_query,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    thinking_config=types.ThinkingConfig(
                        thinking_level=types.ThinkingLevel.LOW 
                    )
                )
            )
            
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logging.error(f"Streaming error: {e}")
            yield f"I'm sorry, I encountered an error: {str(e)}"

    return Response(stream_with_context(generate()), mimetype='text/plain')
