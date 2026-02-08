import streamlit as st

def render_settings(app):
    st.header("Settings Module")
    st.info("Module under construction. AuthManager integration coming next.")
    st.write(f"Current API Key: {app.auth.get_api_key() or 'Not Set'}")