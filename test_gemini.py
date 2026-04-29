import google.generativeai as genai
import os
from dotenv import load_dotenv

# Carga tu clave secreta
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("Modelos habilitados para tu API Key:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)