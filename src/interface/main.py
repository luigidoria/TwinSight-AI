import sys
import os
import streamlit as st

# --- Path Configuration ---
# Resolve the project root directory to ensure absolute imports from 'src' work correctly.
# This allows the script to be executed from any directory without import errors.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))

if project_root not in sys.path:
    sys.path.append(project_root)

# --- Module Imports ---
from src.interface.classes.app_state import TwinSightApp
from src.interface.modules.dashboard import render_dashboard
from src.interface.modules.settings import render_settings
from src.interface.modules.simulation import render_simulation

def main():
    """
    Main application entry point.
    
    Handles the application lifecycle:
    1. Configuration (Page setup).
    2. State Initialization (TwinSightApp singleton).
    3. Global Navigation (Sidebar).
    4. Module Routing (Context-based rendering).
    """
    
    # Configure Streamlit page settings. Must be the first Streamlit command.
    st.set_page_config(
        page_title="TwinSight AI | Industrial Monitor",
        page_icon="factory", 
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize the central application controller.
    # This recovers the state from URL parameters or Session State immediately.
    app = TwinSightApp(is_standalone=True)

    # --- Sidebar Navigation ---
    with st.sidebar:
        # Render branding (Logo or Text fallback).
        logo_path = "src/interface/assets/logo.png"
        if os.path.exists(logo_path):
            st.logo(logo_path)
        else:
            st.title("TwinSight")
        
        # Determine the active sidebar item based on the current application context.
        # 'fleet' and 'asset' contexts both map to 'Monitoring' (index 0).
        if app.context == 'settings':
            initial_index = 2
        elif app.context == 'simulation':
            initial_index = 1
        else:
            initial_index = 0
        
        nav_options = ["Monitoring", "Simulation", "Settings"]
        
        nav_selection = st.radio(
            label="Navigation",
            options=nav_options,
            index=initial_index,
            label_visibility="collapsed"
        )

        # Handle navigation state transitions.
        # Only trigger a rerun if the selection differs from the current active context.
        if nav_selection == "Settings" and app.context != "settings":
            app.context = "settings"
            st.rerun()
            
        elif nav_selection == "Simulation" and app.context != "simulation":
            app.context = "simulation"
            st.rerun()
            
        elif nav_selection == "Monitoring" and app.context not in ["fleet", "asset"]:
            # Default to 'fleet' view when returning to Monitoring.
            app.context = "fleet"
            st.rerun()

        st.divider()
        
        # Debugging State Visualization (remove in production).
        with st.expander("Debug State"):
            st.json({
                "Context": app.context,
                "Asset ID": app.selected_asset_id,
                "API Key": "Set" if app.auth.get_api_key() else "Missing"
            })

    # --- Application Routing ---
    # Delegate rendering to the specific module based on the current context.
    if app.context == "settings":
        render_settings(app)
    elif app.context == "simulation":
        render_simulation(app)
    else:
        # The dashboard module handles both 'fleet' (overview) and 'asset' (drill-down) views.
        render_dashboard(app)

if __name__ == "__main__":
    main()