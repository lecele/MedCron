import google.generativeai as genai
import os
from app.core.config import get_settings

settings = get_settings()
genai.configure(api_key=settings.google_api_key)

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
