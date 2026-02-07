import time
import logging

from src.modules.data.database_handler import DatabaseHandler
from src.modules.machines.motor import MotorSimulator

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("TwinSight-Orchestrator")

def run_simulation():
    """
    Orchestrates the simulation of multiple industrial assets 
    and persists telemetry data to the local database.
    """
    
    # 1. Initialize Infrastructure
    # Ensure the DB path matches your setup
    db = DatabaseHandler("sensors.db")
    logger.info("Infrastructure initialized.")

    # 2. Initialize Assets (Digital Twins)
    # Motor 1: Standard operation
    motor_01 = MotorSimulator(
        motor_id="MTR-01-CONVEYOR", 
        base_rpm=1750, 
        initial_load=0.8
    )
    
    # Motor 2: High speed, heavier load (Ex: Industrial Fan)
    motor_02 = MotorSimulator(
        motor_id="MTR-02-FAN", 
        base_rpm=3500, 
        initial_load=0.95
    )

    assets = [motor_01, motor_02]

    try:
        # 3. Start Sequence
        logger.info("Starting production line...")
        for asset in assets:
            asset.start()

        # 4. Simulation Loop (Generate & Ingest)
        cycles_to_run = 10
        logger.info(f"Running simulation for {cycles_to_run} cycles...")

        for i in range(cycles_to_run):
            for asset in assets:
                # Generate Telemetry (Physics Calculation)
                telemetry_packet = asset.get_telemetry()
                
                # Persist to Database
                db.save_reading(telemetry_packet)
            
            # Simulate sampling rate
            time.sleep(0.5)

        # 5. Stop Sequence
        logger.info("Stopping production line...")
        for asset in assets:
            asset.stop()

        # 6. Verification (Read back from DB)
        # Using logging instead of print allows silencing this output via config
        logger.info("="*60)
        logger.info("LATEST 10 TELEMETRY RECORDS (DATABASE VERIFICATION)")
        logger.info("="*60)
        
        # Header formatting
        header = f"{'ID':<5} | {'TIMESTAMP':<20} | {'MOTOR_ID':<15} | {'RPM':<6} | {'TEMP':<6}"
        logger.info(header)
        logger.info("-" * len(header))

        rows = db.get_recent_readings(limit=10)
        
        # Display formatted rows via Logger
        for row in rows:
            # Unpacking based on DB Schema:
            # (id, motor_id, timestamp, status, load_pct, speed_rpm, temperature_c, vibration_mm_s, degradation_level)
            r_id, r_motor, r_time, _, _, r_speed, r_temp, _, _ = row
            
            # Extract time only (HH:MM:SS) from ISO format for cleaner log
            time_str = r_time[11:19] if len(r_time) > 19 else r_time
            
            logger.info(f"{r_id:<5} | {time_str:<20} | {r_motor:<15} | {r_speed:<6} | {r_temp:<6.1f}")

    except KeyboardInterrupt:
        logger.warning("Simulation stopped by user.")
    except Exception as e:
        logger.error(f"Critical simulation error: {e}", exc_info=True)
    finally:
        db.close()
        logger.info("Simulation finished.")

if __name__ == "__main__":
    run_simulation()