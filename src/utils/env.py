import os
import logging
from dotenv import load_dotenv, set_key, find_dotenv
from pathlib import Path

# Configure module-level logger
logger = logging.getLogger("TwinSight-EnvLoader")

def load_config() -> dict:
    """
    Loads environment variables from the .env file.
    
    Expected Structure:
    - API_URL: Base URL for the LLM provider.
    - API_KEY: Authentication token.
    - MODEL_FOR_TEXT: Main model for analysis/chat.
    - MODEL_FOR_JSON: Specialized model for structured data extraction.
    - VALIDATION_MODEL: Lightweight model used solely for connection testing.
    """
    env_path = find_dotenv()
    
    if not env_path:
        logger.warning("Configuration file (.env) not found. Relying on system environment variables.")
    else:
        load_dotenv(env_path, override=True)

    return {
        "API_URL": os.getenv("API_URL"),
        "API_KEY": os.getenv("API_KEY"),
        "MODEL_FOR_TEXT": os.getenv("MODEL_FOR_TEXT"),
        "MODEL_FOR_JSON": os.getenv("MODEL_FOR_JSON"),
        "VALIDATION_MODEL": os.getenv("VALIDATION_MODEL"),
    }

def update_env_variable(key: str, value: str):
    """Updates or adds a specific variable to the local .env file."""
    try:
        env_path = find_dotenv()
        
        if not env_path:
            root_dir = Path(__file__).resolve().parent.parent.parent
            env_path = root_dir / ".env"
            env_path.touch()

        set_key(str(env_path), key, value)
        load_dotenv(env_path, override=True)
        
    except Exception as e:
        logger.error(f"Failed to write to .env file: {str(e)}")