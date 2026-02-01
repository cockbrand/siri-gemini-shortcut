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

    location_context = f" The user is roughly at coordinates {lat}, {lon}. Take their location into account and use your local knowledge if relevant for the response." if lat and lon else ""

    def generate():
        try:
            # Using generate_content_stream for real-time chunks
            response_stream = client.models.generate_content_stream(
                model='gemini-3-flash-preview',
                contents=user_query,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        f"You are a digital assistant whose response is read out on a device. Make sure to keep your response concise and on point. {location_context}" 
                        "Use metric units. "
                        "Assume that the user is male if relevant for your response and not indicated otherwise."
                    ),
                    # Set thinking to LOW for maximum streaming speed
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
            yield f"Error: {str(e)}"

    # Return a streaming response that Flask handles
    return Response(stream_with_context(generate()), mimetype='text/plain')
