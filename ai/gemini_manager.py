import streamlit as st
import google.generativeai as genai
from typing import Iterator

def get_gemini_api_key() -> str:
    """Retrieve Gemini API Key from session state override or secrets."""
    session_key = st.session_state.get("user_gemini_api_key", "")
    if session_key and session_key.strip():
        return session_key.strip()
    try:
        if "GEMINI_API_KEY" in st.secrets:
            key = st.secrets["GEMINI_API_KEY"]
            if key and key.strip():
                return key.strip()
    except Exception:
        pass

    try:
        import os
        secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".streamlit", "secrets.toml")
        if os.path.exists(secrets_path):
            with open(secrets_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("GEMINI_API_KEY"):
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            val = parts[1].strip().strip('"').strip("'")
                            if val:
                                return val
    except Exception:
        pass

    return ""

def is_gemini_configured() -> bool:
    """Check if a valid Gemini API Key is configured."""
    key = get_gemini_api_key()
    if not key:
        return False
    key_clean = key.strip()
    if not key_clean:
        return False
    # Check for placeholder values
    key_upper = key_clean.upper()
    if any(p in key_upper for p in ["YOUR_API_KEY", "PLACEHOLDER", "YOUR_KEY", "ENTER_KEY", "YOUR_GEMINI_API_KEY"]):
        return False
    # Check for minimum key length
    if len(key_clean) < 15:
        return False
    return True

def init_gemini() -> bool:
    """Initialize Gemini connection."""
    if not is_gemini_configured():
        return False
    key = get_gemini_api_key()
    try:
        genai.configure(api_key=key)
        return True
    except Exception:
        return False

def get_best_available_model() -> str:
    """Retrieve the best available flash model supported by the API key."""
    try:
        models = [m.name for m in genai.list_models()]
        for candidate in ["models/gemini-3.5-flash", "models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-1.5-flash", "models/gemini-flash-latest"]:
            if candidate in models:
                return candidate.replace("models/", "")
    except Exception:
        pass
    return "gemini-2.5-flash"

def generate_response_stream(prompt: str, system_instruction: str = "") -> Iterator[str]:
    """Stream response from Gemini model."""
    if not init_gemini():
        yield "❌ AI API Key is not configured. Please add your API key in .streamlit/secrets.toml."
        return
        
    try:
        model_name = get_best_available_model()
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction if system_instruction else None
        )
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"❌ Error communicating with AI service: {str(e)}"
