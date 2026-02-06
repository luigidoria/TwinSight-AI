import sys
import os
import random
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from typing import Dict

# --- Configuration ---
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/modules/data/sensors.db'))
NUM_MOTORS = 50
DAYS_HISTORY = 180
INTERVAL_MINUTES = 60 
BATCH_SIZE = 5000

# --- State Constants ---
STATE_HEALTHY = 0
STATE_FAILING = 1
STATE_REPAIRING = 2

def get_base_specs(motor_type: str) -> Dict:
    """Returns base physics parameters for different asset types."""
    if motor_type == "CONVEYOR":
        return {"rpm": 1750, "temp": 55.0, "vib": 1.2, "heat_coeff": 15.0}
    elif motor_type == "FAN":
        return {"rpm": 3600, "temp": 48.0, "vib": 2.5, "heat_coeff": 10.0}
    elif motor_type == "PUMP":
        return {"rpm": 1200, "temp": 42.0, "vib": 0.8, "heat_coeff": 12.0}
    return {"rpm": 1800, "temp": 50.0, "vib": 1.0, "heat_coeff": 10.0}

def generate_lifecycle_data():
    print(f"--- STARTING LIFECYCLE SEEDING: {NUM_MOTORS} Assets over {DAYS_HISTORY} Days ---")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Updated Schema to match the requirement
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            motor_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            status TEXT NOT NULL,
            load_pct REAL,
            speed_rpm INTEGER,
            temperature_c REAL,
            vibration_mm_s REAL,
            degradation_level REAL
        );
    """)

    start_date = datetime.now() - timedelta(days=DAYS_HISTORY)
    total_steps = int((DAYS_HISTORY * 24 * 60) / INTERVAL_MINUTES)
    
    records_buffer = []
    total_inserted = 0

    for i in range(1, NUM_MOTORS + 1):
        motor_type = random.choice(["CONVEYOR", "FAN", "PUMP"])
        motor_id = f"MTR-{i:03d}-{motor_type[:3]}"
        specs = get_base_specs(motor_type)
        
        # --- Lifecycle State Initialization ---
        current_state = STATE_HEALTHY
        
        # Random initialization to avoid all motors breaking at the same time
        steps_until_change = random.randint(50, 2000) 
        
        # Degradation accumulators
        wear_factor = 0.0  # Affects vibration
        clog_factor = 0.0  # Affects temperature
        
        # Current active fault type (None if healthy)
        current_fault_type = None

        curr_time = start_date
        
        # Progress indicator
        if i % 10 == 0:
            print(f"Processing Asset {i}/{NUM_MOTORS}: {motor_id}...")

        for step in range(total_steps):
            # 1. State Machine Transition Logic
            steps_until_change -= 1
            
            if steps_until_change <= 0:
                if current_state == STATE_HEALTHY:
                    # Transition: Healthy -> Failing
                    current_state = STATE_FAILING
                    current_fault_type = random.choice(["BEARING_WEAR", "COOLING_FAIL", "LOOSE_FOOT", "MULTI"])
                    # Failure develops over 3 to 15 days
                    steps_until_change = random.randint(216, 1080) 
                    
                elif current_state == STATE_FAILING:
                    # Transition: Failing -> Repairing (Maintenance Event)
                    current_state = STATE_REPAIRING
                    # Maintenance takes 4 to 12 hours
                    steps_until_change = random.randint(12, 36) 
                    
                elif current_state == STATE_REPAIRING:
                    # Transition: Repairing -> Healthy
                    current_state = STATE_HEALTHY
                    # Reset degradation factors (simulating repair)
                    wear_factor = 0.0
                    clog_factor = 0.0
                    current_fault_type = None
                    # Stays healthy for 20 to 60 days
                    steps_until_change = random.randint(1440, 4320)

            # 2. Degradation Physics (Active only in FAILING state)
            if current_state == STATE_FAILING:
                if current_fault_type in ["BEARING_WEAR", "MULTI", "LOOSE_FOOT"]:
                    wear_factor += random.uniform(0.002, 0.008)
                if current_fault_type in ["COOLING_FAIL", "MULTI"]:
                    clog_factor += random.uniform(0.05, 0.15)
            
            # 3. Environmental & Load Simulation
            # Daily temperature cycle (sine wave)
            hour_noise = np.sin((curr_time.hour - 6) * np.pi / 12)
            ambient_temp = 25.0 + (hour_noise * 5.0) + random.uniform(-1, 1)
            
            # Shift Logic: Higher load between 08:00 and 18:00
            is_shift = 8 <= curr_time.hour <= 18
            base_load = random.uniform(0.6, 0.95) if is_shift else random.uniform(0.1, 0.4)
            
            # If repairing, load is zero (machine stopped)
            if current_state == STATE_REPAIRING:
                base_load = 0.0
                rpm_val = 0
                vib_val = 0.0
                temp_val = ambient_temp # Cools down to ambient
            else:
                # Normal operation physics
                rpm_val = int(specs["rpm"] * (1 - (0.02 * base_load)))
                
                # Vibration = Base + Load Factor + Wear
                vib_val = specs["vib"] + (base_load * 0.5) + wear_factor + random.uniform(-0.05, 0.05)
                
                # Loose foot adds random spikes
                if current_fault_type == "LOOSE_FOOT" and current_state == STATE_FAILING and random.random() < 0.1:
                    vib_val += random.uniform(2.0, 5.0)

                # Temperature = Ambient + (Load * Efficiency) + Clog
                temp_val = ambient_temp + (base_load * specs["heat_coeff"]) + clog_factor + random.uniform(-0.5, 0.5)

            # 4. Metric Calculation & Normalization
            
            # Status Determination based on thresholds
            status_label = "NORMAL"
            if current_state == STATE_REPAIRING:
                status_label = "MAINTENANCE"
            elif temp_val > 80.0 or vib_val > 5.0:
                status_label = "CRITICAL"
            elif temp_val > 65.0 or vib_val > 3.5:
                status_label = "WARNING"

            # Degradation Level (Synthetic 0-100 metric for AI analysis)
            # 0 = Brand New, 100 = Total Failure
            deg_calc = (wear_factor * 15) + (clog_factor * 2)
            degradation_level = min(100.0, max(0.0, deg_calc))

            # Buffer append (Mapping to new Schema)
            records_buffer.append((
                motor_id,
                curr_time.strftime("%Y-%m-%d %H:%M:%S"),
                status_label,
                round(base_load * 100, 2), # load_pct (0-100)
                rpm_val,                   # speed_rpm
                round(temp_val, 2),        # temperature_c
                round(vib_val, 2),         # vibration_mm_s
                round(degradation_level, 2)
            ))

            curr_time += timedelta(minutes=INTERVAL_MINUTES)

            # Batch Insert Strategy
            if len(records_buffer) >= BATCH_SIZE:
                try:
                    cursor.executemany("""
                        INSERT INTO telemetry (
                            motor_id, timestamp, status, load_pct, 
                            speed_rpm, temperature_c, vibration_mm_s, degradation_level
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, records_buffer)
                    conn.commit()
                    
                    if cursor.rowcount == len(records_buffer):
                        total_inserted += len(records_buffer)
                    
                    records_buffer = [] # Clear buffer
                    
                except sqlite3.Error as e:
                    print(f"CRITICAL DB ERROR: {e}")
                    conn.rollback()

    # Final commit for remaining records
    if records_buffer:
        cursor.executemany("""
            INSERT INTO telemetry (
                motor_id, timestamp, status, load_pct, 
                speed_rpm, temperature_c, vibration_mm_s, degradation_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, records_buffer)
        conn.commit()
        total_inserted += len(records_buffer)

    conn.close()
    print("="*60)
    print(f"LIFECYCLE SEEDING COMPLETE. Inserted {total_inserted} records.")
    print(f"Simulation covered {DAYS_HISTORY} days with multiple failure/repair cycles.")
    print("="*60)

if __name__ == "__main__":
    generate_lifecycle_data()