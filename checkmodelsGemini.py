import google.generativeai as genai
from config import GEMINI_API_KEY # Asegúrate de que importe tu key

genai.configure(api_key=GEMINI_API_KEY)

print("🔍 Buscando modelos disponibles...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"✅ {m.name}")