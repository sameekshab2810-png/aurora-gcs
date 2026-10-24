from __future__ import annotations

import math
import threading
import time
from typing import Any


class DroneSimulation:
    """Mission drone model for simulated motion and checkpoint logic."""

    def __init__(self, base_position: tuple[float, float], movement_speed: float = 14.0):
        self.lock = threading.RLock()
        self.base_position = (float(base_position[0]), float(base_position[1]))
        self.position = self.base_position
        self.movement_speed = float(movement_speed)
        self.waypoint_tolerance = 1.5
        self.current_waypoint: tuple[float, float] | None = None
        self.heading = 0.0
        self._last_update = time.monotonic()

    def set_position(self, x: float, y: float) -> None:
        self.position = (float(x), float(y))

    def set_waypoint(self, waypoint: tuple[float, float] | None) -> None:
        self.current_waypoint = waypoint
        if waypoint is None:
            self.heading = 0.0
            return
        dx = waypoint[0] - self.position[0]
        dy = waypoint[1] - self.position[1]
        if dx == 0 and dy == 0:
            self.heading = 0.0
        else:
            self.heading = math.degrees(math.atan2(dy, dx))

    def step_toward_target(self, target: tuple[float, float], dt: float) -> tuple[float, float]:
        if dt <= 0:
            return self.position
        target_x, target_y = target
        dist_x = target_x - self.position[0]
        dist_y = target_y - self.position[1]
        distance = math.hypot(dist_x, dist_y)
        if distance <= self.waypoint_tolerance:
            self.position = (target_x, target_y)
            return self.position
        step = min(self.movement_speed * dt, distance)
        if distance == 0:
            return self.position
        ratio = step / distance
        new_x = self.position[0] + dist_x * ratio
        new_y = self.position[1] + dist_y * ratio
        self.position = (new_x, new_y)
        return self.position

    def distance_to(self, point: tuple[float, float]) -> float:
        return math.hypot(point[0] - self.position[0], point[1] - self.position[1])

    def at_target(self, point: tuple[float, float]) -> bool:
        return self.distance_to(point) <= self.waypoint_tolerance

    def snapshot(self) -> dict[str, Any]:
        return {
            'x': round(self.position[0], 3),
            'y': round(self.position[1], 3),
            'base_x': round(self.base_position[0], 3),
            'base_y': round(self.base_position[1], 3),
            'heading': round(self.heading, 2),
            'waypoint': self.current_waypoint,
        }
