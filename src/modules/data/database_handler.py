import sqlite3
import logging
import os
from typing import Dict, List, Any, Optional

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TwinSight-DB")

class DatabaseHandler:
    """
    Handles SQLite database operations for the TwinSight-AI project.
    Thread-safe and robust handling of paths and connections.
    """

    def __init__(self, db_name: str = "sensors.db"):
        # Define absolute path based on project root
        # This ensures it works regardless of where the script is executed
        self.project_root = os.getcwd() 
        self.data_dir = os.path.join(self.project_root, "src", "modules", "data")
        self.db_path = os.path.join(self.data_dir, db_name)
        
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

        # Ensure the directory exists before attempting to connect
        self._ensure_directory()

    def _ensure_directory(self):
        """Creates the data directory if it doesn't exist."""
        if not os.path.exists(self.data_dir):
            try:
                os.makedirs(self.data_dir)
                logger.info(f"Created data directory at: {self.data_dir}")
            except OSError as e:
                logger.error(f"Failed to create directory {self.data_dir}: {e}")

    def connect(self):
        """Establishes connection to the SQLite database."""
        try:
            # check_same_thread=False is necessary if Streamlit runs on another thread
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.connection.cursor()
            logger.info(f"Connected to database at {self.db_path}")
            
            # Ensure the table schema exists upon connection
            self._create_table()
            
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")

    def _create_table(self):
        """Internal method to initialize the schema."""
        create_table_query = """
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
        """
        if self.cursor:
            self.cursor.execute(create_table_query)
            self.connection.commit()

    def save_reading(self, data: Dict[str, Any]):
        """
        Inserts a single dictionary reading into the database.
        Maps dictionary keys to SQL columns explicitly to avoid ordering errors.
        """
        if not self.connection:
            self.connect()

        insert_query = """
        INSERT INTO telemetry (
            motor_id, timestamp, status, load_pct, 
            speed_rpm, temperature_c, vibration_mm_s, degradation_level
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """

        # Transform Dict to Tuple in EXACT column order
        # This fixes type incompatibility issues with sqlite3
        params = (
            data.get("motor_id"),
            data.get("timestamp"),
            data.get("status"),
            data.get("load_pct"),
            data.get("speed_rpm"),
            data.get("temperature_c"),
            data.get("vibration_mm_s"),
            data.get("degradation_level")
        )

        try:
            self.cursor.execute(insert_query, params)
            self.connection.commit()
            # logger.debug(f"Saved reading for {data.get('motor_id')}") # Verbose logging
        except sqlite3.Error as e:
            logger.error(f"Error inserting data: {e}")

    def get_recent_readings(self, motor_id: Optional[str] = None, limit: int = 50) -> List[tuple]:
        """Fetch historical data for the frontend."""
        if not self.cursor:
            self.connect()

        select_query = "SELECT * FROM telemetry"
        params = []
        
        if motor_id:
            select_query += " WHERE motor_id = ?"
            params.append(motor_id)
            
        select_query += " ORDER BY timestamp DESC, id DESC LIMIT ?"
        params.append(limit)
        
        try:
            self.cursor.execute(select_query, params)
            rows = self.cursor.fetchall()
            return rows
        except sqlite3.Error as e:
            logger.error(f"Error retrieving data: {e}")
            return []

    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed.")