import random
import time
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any

class MotorSensor(ABC):
    """
    Abstract Base Class defining the contract for any motor sensor system.
    This ensures that whether we use a Simulator or a Real Sensor (in the future),
    the interface remains consistent.
    """

    def __init__(self, motor_id: str):
        self.motor_id = motor_id
        self.speed: int = 0
        self.temperature: float = 25.0  # Initial temperature in Celsius
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