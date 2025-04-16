import google.generativeai as genai
import os
import json

genai.configure(api_key=os.environ.get("GEMINI_API", ""))

model = genai.GenerativeModel("gemini-1.5-flash")

PROMPT = "Generate a JSON object with 'title' and 'description' for this image."

def test_gemini():
    response = model.generate_content(PROMPT)

    try:
        json_data = json.loads(response.text)
        print("Gemini Response:", json_data)
    except ValueError:
        print("ERROR: Geminin did not return valid JSON")

test_gemini()