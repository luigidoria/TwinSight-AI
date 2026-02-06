import os
import sys
from dotenv import load_dotenv
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
logger = logging.getLogger("TwinSight-Orchestrator")

def get_environment() -> dict:
    """
    Loads environment variables from a .env file and returns them as a dictionary.
    Expected variables: API_URL, API_KEY, MODEL_FOR_TEXT, MODEL_FOR_JSON
    """
    
    loaded = load_dotenv()
    
    if not loaded:
        logger.error("File: .env not found or empty. Please ensure it exists and contains the necessary variables.")
        return {}
    
    api_url = os.getenv("API_URL")
    secret_key = os.getenv("API_KEY")
    model_text = os.getenv("MODEL_FOR_TEXT")
    model_json = os.getenv("MODEL_FOR_JSON")

    return {
        "API_URL": api_url,
        "API_KEY": secret_key,
        "MODEL_FOR_TEXT": model_text,
        "MODEL_FOR_JSON": model_json
    }
    
if __name__ == "__main__":
    get_environment()