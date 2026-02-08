import streamlit as st
from typing import Optional, Dict, Any
from src.interface.classes.auth_manager import AuthManager

class TwinSightApp:
    """
    Central Application Controller.
    
    This class acts as a singleton proxy between the User Interface and Streamlit's 
    Session State. It manages global state persistence, URL synchronization, 
    and authentication context.
    """

    def __init__(self, is_standalone: bool = True):
        self.prefix = 'ts_'
        self.auth = AuthManager(self.prefix)
        self.is_standalone = is_standalone 

        # Initialize state immediately upon instantiation to ensure
        # consistency between URL and Session State.
        self._init_state()

    def _get_state(self, key: str, default: Any = None) -> Any:
        """Retrieves a value from Session State using the secure namespace prefix."""
        return st.session_state.get(f"{self.prefix}{key}", default)

    def _set_state(self, key: str, value: Any):
        """Writes a value to Session State using the secure namespace prefix."""
        st.session_state[f"{self.prefix}{key}"] = value

    def _sync_url(self, key: str, value: Optional[str]):
        """
        Updates the browser URL query parameters.
        If the value is None or empty, the parameter is removed from the URL.
        """
        if value:
            st.query_params[key] = str(value)
        elif key in st.query_params:
            del st.query_params[key]

    def _init_state(self):
        """
        Initializes the application state based on priority precedence:
        1. URL Query Parameters (Deep Linking)
        2. Existing Session State (Browser Refresh/F5)
        3. Default Values (First Load)
        """
        
        # --- 1. View Context (Fleet vs. Asset) ---
        url_view = st.query_params.get('view')
        session_view = self._get_state('view')
        
        # Logic: If URL exists, it wins. Else, check session. Else, default to 'fleet'.
        final_view = url_view or session_view or 'fleet'
        
        self._set_state('view', final_view)
        self._sync_url('view', final_view)

        # --- 2. Asset Selection ---
        url_asset = st.query_params.get('asset_id')
        session_asset = self._get_state('asset_id')
        
        final_asset = url_asset or session_asset or None
        
        self._set_state('asset_id', final_asset)
        self._sync_url('asset_id', final_asset)

        # --- 3. Filters (Session Persistence Only) ---
        # Filters are not synced to URL initially to avoid complexity with JSON serialization.
        if self._get_state('filters') is None:
            default_filters = {
                'date_range': None,
                'asset_type': [],
                'status': []
            }
            self._set_state('filters', default_filters)
    
    @property
    def context(self) -> str:
        """Gets the current view context ('fleet' or 'asset')."""
        return self._get_state('view', 'fleet')

    @context.setter
    def context(self, new_view: str):
        """Sets the view context and updates the URL."""
        self._set_state('view', new_view)
        self._sync_url('view', new_view)

    @property
    def selected_asset_id(self) -> Optional[str]:
        """Gets the currently selected asset ID."""
        return self._get_state('asset_id')

    @selected_asset_id.setter
    def selected_asset_id(self, new_id: Optional[str]):
        """Sets the selected asset ID and updates the URL."""
        self._set_state('asset_id', new_id)
        self._sync_url('asset_id', new_id)

    @property
    def filters(self) -> Dict:
        """Gets the active filter configuration."""
        return self._get_state('filters', {})

    @filters.setter
    def filters(self, new_filters: Dict):
        """Sets the active filters (Persisted in Session State only)."""
        self._set_state('filters', new_filters)