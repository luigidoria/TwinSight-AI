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
    2. UI Customization (CSS injection).
    3. State Initialization (TwinSightApp singleton).
    4. Global Navigation (Sidebar).
    5. Module Routing (Context-based rendering).
    """
    
    # Configure Streamlit page settings. Must be the first Streamlit command.
    st.set_page_config(
        page_title="TwinSight AI | Industrial Monitor",
        page_icon="factory", 
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # --- UI Customization (CSS) ---
    # Injects custom CSS to control the layout and visibility of Streamlit elements.
    # 1. Hides the 'Deploy' button.
    # 2. Hides the 'Main Menu' (three dots).
    # 3. Forces the Sidebar to a compact width (250px).
    st.markdown("""
        <style>
            .stDeployButton {display: none;}
            #MainMenu {visibility: hidden;}
            
            section[data-testid="stSidebar"] {
                min-width: 250px !important;
                max-width: 250px !important;
            }
        </style>
    """, unsafe_allow_html=True)

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
        
        st.markdown("### Navigation")

        # Navigation Buttons
        # We use standard buttons instead of radio for a cleaner look.
        # The 'type' parameter is used to highlight the active context.
        
        # 1. Monitoring Button
        # Active if context is 'fleet' or 'asset'
        is_monitoring = app.context in ['fleet', 'asset']
        if st.button("Monitoring", width='stretch', type="primary" if is_monitoring else "secondary"):
            if app.context not in ['fleet', 'asset']:
                app.context = "fleet"
                st.rerun()

        # 2. Simulation Button
        is_simulation = app.context == 'simulation'
        if st.button("Simulation", width='stretch', type="primary" if is_simulation else "secondary"):
            if app.context != 'simulation':
                app.context = "simulation"
                st.rerun()

        # 3. Settings Button
        is_settings = app.context == 'settings'
        if st.button("Settings", width='stretch', type="primary" if is_settings else "secondary"):
            if app.context != 'settings':
                app.context = "settings"
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