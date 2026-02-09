import streamlit as st

def render_simulation(app):
    st.header("⚙️ Data Generation Engine")
    st.markdown("""
    Configure the parameters for the **Historical Data Seeder**. 
    This module generates synthetic telemetry data representing the lifecycle of industrial assets 
    (Healthy -> Failing -> Repairing).
    """)

    # Retrieve current config from App State
    config = app.simulation_config

    with st.form("simulation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Asset Configuration")
            
            # Aligned with get_base_specs in data_seeder.py
            asset_type = st.selectbox(
                "Asset Type",
                options=["PUMP", "FAN", "CONVEYOR"],
                index=0, 
                help="Defines the physical baseline (RPM, Vibration, Temperature) for the simulation."
            )
            
            asset_count = st.number_input(
                "Number of Assets",
                min_value=1,
                max_value=50,
                value=config.get('asset_count', 5),
                help="How many distinct motor IDs to generate."
            )

        with col2:
            st.subheader("Time Domain")
            
            # Aligned with DAYS_HISTORY
            duration = st.slider(
                "History Duration (Days)",
                min_value=30,
                max_value=365,
                value=config.get('duration_days', 180),
                help="Total historical period to simulate."
            )
            
            # Aligned with INTERVAL_MINUTES
            interval = st.select_slider(
                "Sampling Interval (Minutes)",
                options=[15, 30, 60, 120, 240],
                value=config.get('interval_minutes', 60),
                help="Frequency of telemetry data points."
            )

        st.markdown("---")
        
        # Form Submission
        submitted = st.form_submit_button("Generate Synthetic Data", type="primary")
        
        if submitted:
            # Update the Global State
            new_config = {
                'asset_type': asset_type,
                'asset_count': asset_count,
                'duration_days': duration,
                'interval_minutes': interval
            }
            app.simulation_config = new_config
            
            # UX Feedback
            st.success(f"Configuration saved! Ready to generate {duration} days of history for {asset_count} {asset_type}(s).")
            st.info("Note: Actual database seeding will be triggered in the next step (Backend Integration).")