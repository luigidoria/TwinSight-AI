import sqlite3
import pandas as pd
import os
import logging
from typing import Optional, Dict

# Configure logger
logger = logging.getLogger("TwinSight-DataManager")

class DataManager:
    """
    Data Access Layer (DAL) for the TwinSight Dashboard.
    
    This class is optimized for READ operations using Pandas.
    It abstracts complex SQL aggregation logic from the frontend modules.
    """

    def __init__(self, db_name: str = "sensors.db"):
        # 1. Path Resolution (Same logic as your DatabaseHandler for consistency)
        # Assuming this file is in src/modules/data/
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(current_dir, db_name)
        
        # Verify if DB exists to avoid silent failures
        if not os.path.exists(self.db_path):
            logger.warning(f"Database not found at {self.db_path}. Dashboard will be empty.")

    def _get_connection(self):
        """Creates a temporary connection for read operations."""
        try:
            # URI mode allows for read-only access if needed, but standard connect is fine
            conn = sqlite3.connect(self.db_path)
            return conn
        except sqlite3.Error as e:
            logger.error(f"Connection failed: {e}")
            return None

    def get_fleet_snapshot(self) -> pd.DataFrame:
        """
        Retrieves the LATEST telemetry record for every unique motor.
        Essential for the main Fleet Dashboard table.
        """
        query = """
        SELECT 
            t.motor_id,
            t.timestamp,
            t.status,
            t.load_pct,
            t.speed_rpm,
            t.temperature_c,
            t.vibration_mm_s,
            t.degradation_level
        FROM telemetry t
        INNER JOIN (
            SELECT motor_id, MAX(timestamp) as max_ts
            FROM telemetry
            GROUP BY motor_id
        ) latest ON t.motor_id = latest.motor_id AND t.timestamp = latest.max_ts
        ORDER BY t.motor_id ASC;
        """
        
        try:
            conn = self._get_connection()
            if not conn: return pd.DataFrame()
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            # Data Enrichment: Extract Asset Type (e.g., 'PUMP' from 'MTR-01-PUMP')
            if not df.empty and 'motor_id' in df.columns:
                df['asset_type'] = df['motor_id'].apply(lambda x: x.split('-')[-1] if '-' in x else 'GENERIC')
                
            return df
            
        except Exception as e:
            logger.error(f"Error fetching snapshot: {e}")
            return pd.DataFrame()

    def get_kpi_summary(self, df_snapshot: Optional[pd.DataFrame] = None) -> Dict:
        """
        Calculates high-level KPIs (Total, Critical, Healthy) from the snapshot.
        Avoids querying the DB twice if we already have the table data.
        """
        if df_snapshot is None:
            df_snapshot = self.get_fleet_snapshot()
            
        if df_snapshot.empty:
            return {
                "total_assets": 0,
                "healthy": 0,
                "warning": 0,
                "critical": 0,
                "avg_health": 0.0
            }
            
        return {
            "total_assets": len(df_snapshot),
            "healthy": len(df_snapshot[df_snapshot['status'] == 'NORMAL']),
            "warning": len(df_snapshot[df_snapshot['status'] == 'WARNING']),
            "critical": len(df_snapshot[df_snapshot['status'].isin(['CRITICAL', 'MAINTENANCE'])]),
            # Convert Degradation (0=New) to Health Score (100=New)
            "avg_health": round(100 - df_snapshot['degradation_level'].mean(), 1)
        }

    def get_asset_history(self, motor_id: str, days: int = 7) -> pd.DataFrame:
        """
        Retrieves time-series data for a specific asset.
        Used for the Drill-Down charts (Vibration/Temp over time).
        """
        query = """
        SELECT timestamp, load_pct, speed_rpm, temperature_c, vibration_mm_s, degradation_level, status
        FROM telemetry 
        WHERE motor_id = ? 
        AND timestamp >= datetime('now', ?)
        ORDER BY timestamp ASC
        """
        
        try:
            conn = self._get_connection()
            if not conn: return pd.DataFrame()
            
            time_modifier = f"-{days} days"
            df = pd.read_sql_query(query, conn, params=(motor_id, time_modifier))
            conn.close()
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
            return df
            
        except Exception as e:
            logger.error(f"Error fetching history for {motor_id}: {e}")
            return pd.DataFrame()