import os
import google.generativeai as genai
from flask import jsonify
import logging

def siri_gemini(request):
    """HTTP Cloud Function to interact with Gemini."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "GEMINI_API_KEY environment variable not set."}), 500

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    request_json = request.get_json(silent=True)
    if request_json and 'query' in request_json:
        query = request_json['query']
        query += " Respond concisely and like you are an electronic assistant whose response is read out on a device. Use metric units by default."
        logging.info(f"Q: {query}")
        try:
            response = model.generate_content(query)
            logging.info(f"A: {response}")
            return jsonify({"response": response.text})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Missing 'query' in request body."}), 400
