import streamlit as st
import logging
from typing import Optional, Literal
from openai import OpenAI
from src.utils.env import load_config, update_env_variable

logger = logging.getLogger("TwinSight-AuthManager")

class AuthManager:
    def __init__(self, prefix: str):
        """
        Initializes the AuthManager.
        
        Args:
            prefix (str): Namespace prefix for session state (e.g., 'ts_').
        """
        self.prefix = prefix
        
        # Load configuration from .env immediately
        self.config = load_config()

        # Hardcoded fallbacks (Used only if .env is completely missing)
        self._fallback_url = "https://api.groq.com/openai/v1"
        self._fallback_validation_model = "llama-3.3-70b-versatile"

    def get_api_key(self) -> Optional[str]:
        """Retrieves API Key: Local Session > Global Session > Environment."""
        # 1. Local Session
        local = st.session_state.get(f"{self.prefix}api_key")
        if local: return local
        
        # 2. Global Session (Portfolio Injection)
        global_key = st.session_state.get("GLOBAL_API_KEY")
        if global_key: return global_key
        
        # 3. Environment
        return self.config.get("API_KEY")

    def get_api_url(self) -> str:
        """Retrieves API Base URL: Local Session > Environment > Fallback."""
        # 1. Local Session
        local = st.session_state.get(f"{self.prefix}api_url")
        if local: return local
        
        # 2. Environment
        env_url = self.config.get("API_URL")
        if env_url: return env_url
        
        # 3. Fallback
        return self._fallback_url

    def get_model(self, model_type: Literal["text", "json", "validation"]) -> str:
        """
        Retrieves the specific model name based on the use case.
        Acts as a central configuration provider for the entire application.
        
        Args:
            model_type: 'text' (analysis), 'json' (structure), or 'validation' (ping).
        """
        env_key_map = {
            "text": "MODEL_FOR_TEXT",
            "json": "MODEL_FOR_JSON",
            "validation": "VALIDATION_MODEL"
        }
        
        session_key = f"{self.prefix}model_{model_type}"
        env_var_name = env_key_map.get(model_type)

        # 1. Local Session Override
        if st.session_state.get(session_key):
            return st.session_state[session_key]

        # 2. Environment Variable
        if env_var_name and self.config.get(env_var_name):
            return self.config.get(env_var_name)

        # 3. Intelligent Fallbacks
        if model_type == "validation":
            # If no specific validation model, try the text model, then fallback
            return self.get_model("text") or self._fallback_validation_model
        
        return self._fallback_validation_model

    def set_credentials(self, 
                        api_key: Optional[str] = None, 
                        api_url: Optional[str] = None, 
                        model_text: Optional[str] = None, 
                        model_json: Optional[str] = None, 
                        persist: bool = False):
        """
        Updates session state and optionally writes to .env file.
        Arguments are optional to allow partial updates.
        """
        # Update Session State only if value is provided
        if api_key is not None:
            st.session_state[f"{self.prefix}api_key"] = api_key
        if api_url is not None:
            st.session_state[f"{self.prefix}api_url"] = api_url
        if model_text is not None:
            st.session_state[f"{self.prefix}model_text"] = model_text
        if model_json is not None:
            st.session_state[f"{self.prefix}model_json"] = model_json
        
        # Persist to disk if requested
        if persist:
            if api_key: update_env_variable("API_KEY", api_key)
            if api_url: update_env_variable("API_URL", api_url)
            if model_text: update_env_variable("MODEL_FOR_TEXT", model_text)
            if model_json: update_env_variable("MODEL_FOR_JSON", model_json)
            
            logger.info("Credentials persisted to .env file.")
            # Reload config to ensure self.config stays in sync with disk
            self.config = load_config()

    def validate_connection(self) -> tuple[bool, str]:
        """
        Tests the connection using the configured URL, Key, and Validation Model.
        """
        key = self.get_api_key()
        url = self.get_api_url()
        # Explicitly ask for validation model (usually smaller/faster)
        model = self.get_model("validation")
        
        if not key:
            return False, "Missing API Key."
        
        try:
            client = OpenAI(base_url=url, api_key=key)

            client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Ping"},
                    {"role": "user", "content": "Pong"}
                ],
                max_tokens=1,
            )
            
            return True, f"Connected successfully to {url} using {model}"
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Connection validation failed: {error_msg}")
            
            if "401" in error_msg:
                return False, "Error 401: Unauthorized. Check your API Key."
            elif "404" in error_msg:
                return False, f"Error 404: Model '{model}' not found or Invalid URL."
            elif "Connection error" in error_msg:
                 return False, f"Unreachable URL: {url}"
            
            return False, f"Connection error: {error_msg}"