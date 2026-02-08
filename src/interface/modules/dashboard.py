import streamlit as st

def render_dashboard(app):
    st.header(f"Dashboard View: {app.context.upper()}")
    
    if app.context == 'fleet':
        st.write("Displaying Fleet Overview (Table of Motors)")
        if st.button("Simulate Click on Motor MTR-01"):
            app.context = 'asset'
            app.selected_asset_id = 'MTR-01'
            st.rerun()
            
    elif app.context == 'asset':
        st.subheader(f"Analyzing Asset: {app.selected_asset_id}")
        if st.button("⬅ Back to Fleet"):
            app.context = 'fleet'
            app.selected_asset_id = None
            st.rerun()