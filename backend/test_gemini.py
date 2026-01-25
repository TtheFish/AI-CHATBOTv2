import google.generativeai as genai
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('backend/.env')
if not env_path.exists(): env_path = Path('.env')
load_dotenv(env_path)
key = os.getenv("GOOGLE_API_KEY")

with open("test_result.txt", "w") as f:
    if not key:
        f.write("FAILURE: No Key\n")
        exit(1)
    genai.configure(api_key=key)
    
    f.write("Testing gemini-2.0-flash:\n")
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Hello")
        f.write(f"SUCCESS: {response.text}\n")
    except Exception as e:
        f.write(f"ERROR: {e}\n")
