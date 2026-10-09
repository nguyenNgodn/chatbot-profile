import os

import google.generativeai as genai

API_KEY = os.getenv("GEMINI_API_KEY", "")

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel(
    "gemini-3.5-flash-lite"
)

response = model.generate_content(
    "Hello, introduce yourself in one sentence."
)

print(response.text)