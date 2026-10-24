from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SimulationConfig:
    base_position: tuple[float, float] = (0.0, 0.0)
    default_waypoints: tuple[tuple[float, float], ...] = ((30.0, 10.0), (55.0, 20.0), (85.0, 45.0), (110.0, 15.0))
    movement_speed: float = 14.0
    update_rate_hz: int = 30
    waypoint_tolerance: float = 1.5
    max_waypoints: int = 12
    checkpoint_history_limit: int = 200


CONFIG = SimulationConfig()
BASE_DIR = Path(__file__).resolve().parent.parent
