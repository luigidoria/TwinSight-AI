import random
import time
import logging
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any

# --- Logging Configuration ---
#logging.basicConfig(
#    level=logging.INFO,
#    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
#    datefmt="%Y-%m-%d %H:%M:%S"
#)
logger = logging.getLogger("TwinSight-MotorSim")

class MotorSensor(ABC):
    """
    Abstract Base Class defining the contract for any motor sensor system.
    Ensures interface consistency between Simulated and Real hardware.
    """

    def __init__(self, motor_id: str):
        self.motor_id = motor_id
        self.speed: int = 0
        self.temperature: float = 25.0
        self.vibration: float = 0.0
        self._is_running: bool = False

    @abstractmethod
    def start(self) -> None:
        """Starts the motor monitoring/operation."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stops the motor monitoring/operation."""
        pass

    @abstractmethod
    def get_telemetry(self) -> Dict[str, Any]:
        """Returns the current sensor readings."""
        pass

class MotorSimulator(MotorSensor):
    """
    Generates synthetic telemetry data mimicking real motor physics.
    Includes degradation, thermal runaway, load effects, and vibration harmonics.
    """

    # --- Physics Constants (Thresholds & Limits) ---
    TEMP_THRESHOLD_WARNING = 80.0
    VIBRATION_THRESHOLD_WARNING = 5.0
    SPEED_REDUCTION_STEP = 200
    
    # --- Simulation Coefficients ---
    # Heat Physics
    HEAT_RPM_MULTIPLIER = 10.0      # How much RPM contributes to heat
    HEAT_WEAR_MULTIPLIER = 5.0      # How much degradation contributes to heat
    PASSIVE_COOLING_RATE = 0.15     # Degrees lost per cycle naturally
    THERMAL_NOISE_MIN = -0.2
    THERMAL_NOISE_MAX = 0.3

    # Vibration Physics
    VIBRATION_WEAR_MULTIPLIER = 2.0
    MECH_NOISE_MIN = -0.05
    MECH_NOISE_MAX = 0.1
    
    # Degradation Physics
    NORMALIZATION_TEMP = 100.0      # Reference temp for stress calc
    NORMALIZATION_VIB = 2.0         # Reference vib for stress calc
    
    # Speed Physics
    SPEED_NOISE_RANGE = 50          # +/- RPM fluctuation
    MAX_LOAD_SLIP_RPM = 20         # Max RPM drop due to load

    def __init__(self, motor_id: str,  base_rpm: int = 1800, base_temperature: float = 45.0, 
                 base_vibration: float = 0.5, temp_factor: float = 0.02, vibration_factor: float = 0.01,
                 degradation_rate: float = 0.0005, initial_load: float = 0.8):
        
        super().__init__(motor_id)
        
        # Configuration
        self._base_rpm = base_rpm
        self._base_temperature = base_temperature
        self._base_vibration = base_vibration
        
        # Physics Factors
        self._temp_factor = temp_factor
        self._vibration_factor = vibration_factor
        self._degradation_rate = degradation_rate
        
        # State
        self.current_load = initial_load  # 1.0 = Full Load, 0.0 = Idle
        self._degradation_accumulated = 0.0 
        self._cycle_count = 0

    def start(self) -> None:
        self._is_running = True
        self.speed = self._base_rpm
        self.temperature = self._base_temperature
        self.vibration = self._base_vibration
        logger.info(f"Motor {self.motor_id} sequence initiated at {self.current_load*100}% Load.")

    def stop(self) -> None:
        self._is_running = False
        self.speed = 0
        logger.info(f"Motor {self.motor_id} shutdown sequence completed.")

    def set_load(self, load_percentage: float) -> None:
        """Allows dynamic adjustment of motor load (0.0 to 1.0)."""
        self.current_load = max(0.0, min(1.0, load_percentage))
        logger.info(f"Motor {self.motor_id} load adjusted to {self.current_load:.2f}")

    def simulate_cycle(self) -> None:
        """
        Executes one simulation step (physics update).
        Couples Speed, Temperature, Vibration and load using a degradation model.
        """
        if not self._is_running:
            return

        self._cycle_count += 1

        # 1. Physics: Load and Speed Fluctuation
        # Load slightly reduces actual speed (slip)
        load_drag = self.current_load * self.MAX_LOAD_SLIP_RPM 
        speed_noise = random.randint(-self.SPEED_NOISE_RANGE, self.SPEED_NOISE_RANGE)
        target_speed = (self._base_rpm - load_drag) + speed_noise
        
        # 2. Physics: Calculate Degradation Multiplier
        # Stress increases with Temperature, Vibration AND Load
        stress_factor = (
            (self.temperature / self.NORMALIZATION_TEMP) * (self.vibration / self.NORMALIZATION_VIB) *
            (1 + self.current_load) # Load accelerates wear
        )
        current_degradation = self._degradation_rate * (1 + stress_factor)
        self._degradation_accumulated += current_degradation

        # 3. Physics: Update Temperature
        # Heat = Base + (RPM * Factor * Load) + (Wear * Factor) + Noise - Cooling
        heat_from_rpm = (self.speed / self._base_rpm) * self._temp_factor * self.HEAT_RPM_MULTIPLIER * self.current_load
        heat_from_wear = self._degradation_accumulated * self.HEAT_WEAR_MULTIPLIER
        thermal_noise = random.uniform(self.THERMAL_NOISE_MIN, self.THERMAL_NOISE_MAX)
        
        self.temperature += heat_from_rpm + heat_from_wear + thermal_noise - self.PASSIVE_COOLING_RATE

        # 4. Physics: Update Vibration
        # Vibration = Base + (RPM * Factor * Load) + (Wear * Factor) + Noise
        vibration_from_rpm = (self.speed / self._base_rpm) * self._vibration_factor * self.current_load
        vibration_from_wear = self._degradation_accumulated * self.VIBRATION_WEAR_MULTIPLIER
        mech_noise = random.uniform(self.MECH_NOISE_MIN, self.MECH_NOISE_MAX)
        
        self.vibration = self._base_vibration + vibration_from_rpm + vibration_from_wear + mech_noise

        self.speed = max(0, target_speed)

        # 5. Safety Logic
        self._check_safety_thresholds()

    def _check_safety_thresholds(self) -> None:
        """Internal method to handle safety triggers."""
        
        if self.temperature > self.TEMP_THRESHOLD_WARNING:
            self.speed = max(0, self.speed - self.SPEED_REDUCTION_STEP)
            logger.warning(
                f"OVERHEAT ({self.temperature:.2f}°C). Throttling {self.motor_id}."
            )

        if self.vibration > self.VIBRATION_THRESHOLD_WARNING:
            self.speed = max(0, self.speed - self.SPEED_REDUCTION_STEP)
            logger.warning(
                f"HIGH VIBRATION ({self.vibration:.2f} mm/s). Throttling {self.motor_id}."
            )

    def perform_maintenance(self) -> None:
        """Resets degradation and restores optimal conditions."""
        if self._is_running:
            logger.error(f"Maintenance failed: Motor {self.motor_id} is running. Stop motor first.")
            return

        logger.info(f"Maintenance started for Motor {self.motor_id}...")
        self._degradation_accumulated = 0.0
        self.temperature = self._base_temperature
        self.vibration = self._base_vibration
        logger.info(f"Maintenance complete. Motor {self.motor_id} restored to factory condition.")

    def get_telemetry(self) -> Dict[str, Any]:
        """Returns the current state packet."""

        self.simulate_cycle()
        
        return {
            "motor_id": self.motor_id,
            "timestamp": datetime.now().isoformat(),
            "status": "RUNNING" if self._is_running else "STOPPED",
            "load_pct": round(self.current_load * 100, 1), # Added to telemetry
            "speed_rpm": int(self.speed),
            "temperature_c": round(self.temperature, 2),
            "vibration_mm_s": round(self.vibration, 3),
            "degradation_level": round(self._degradation_accumulated, 4)
        }

# --- Unit Test ---
if __name__ == "__main__":
    sim = MotorSimulator(motor_id="TEST-SIM-01")
    sim.start()
    
    try:
        # Simulate 20 cycles
        for i in range(20):
            data = sim.get_telemetry()
            # We don't need to print here because logging is handling output
            # But for debugging purposes, we can print the dict
            # logger.debug(data) 
            
            time.sleep(0.5)
            
            # Force high degradation test on cycle 10
            if i == 10:
                logger.info("Injecting massive wear for testing...")
                sim._degradation_accumulated += 5.0

    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user.")
    finally:
        sim.stop()