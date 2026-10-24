from __future__ import annotations

import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR, CONFIG
from app.drone import DroneSimulation
from app.schemas import AbortInput, WaypointInput
from app.state_machine import MissionState, MissionStateMachine
from app.structures import MissionQueue, MissionStack


class MissionService:
    """Authoritative backend mission controller for queue, stack, and rollback logic."""

    def __init__(self):
        self.lock = threading.RLock()
        self.queue = MissionQueue[tuple[float, float]]()
        self.stack = MissionStack[dict[str, Any]]()
        self.state_machine = MissionStateMachine()
        self.drone = DroneSimulation(CONFIG.base_position, CONFIG.movement_speed)
        self.base_position = CONFIG.base_position
        self.current_waypoint: tuple[float, float] | None = None
        self.active_target: dict[str, Any] | None = None
        self.abort_reason: str | None = None
        self.events: deque[dict[str, Any]] = deque(maxlen=120)
        self.breadcrumbs: list[dict[str, Any]] = []
        self.mission_started_s: float | None = None
        self.simulation_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.simulation_running = False
        self._completed_count = 0
        self._total_waypoints = 0
        self._waypoint_sequence = 0
        self._seed_base_checkpoint()
        self._record_event('INFO', 'Mission prepared.', {'queue_size': self.queue.size()})
        self.reset()

    def _seed_base_checkpoint(self) -> None:
        self.stack.clear()
        base_checkpoint = {
            'x': round(self.base_position[0], 3),
            'y': round(self.base_position[1], 3),
            'sequence': 0,
            'timestamp_ms': self._now_ms(),
            'status': 'BASE',
            'label': 'BASE',
            'id': 'cp-base',
        }
        self.stack.push(base_checkpoint)

    def _checkpoint_payload(self, x: float, y: float, seq: int, status: str, label: str) -> dict[str, Any]:
        return {
            'x': round(x, 3),
            'y': round(y, 3),
            'sequence': seq,
            'timestamp_ms': self._now_ms(),
            'status': status,
            'label': label,
            'id': f'cp-{seq}',
        }

    def _record_event(self, level: str, message: str, details: dict[str, Any] | None = None) -> None:
        entry = {'timestamp_ms': self._now_ms(), 'level': level, 'message': message, 'details': details or {}}
        self.events.append(entry)

    def _now_ms(self) -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _reset_state(self) -> None:
        self.queue.clear()
        for waypoint in CONFIG.default_waypoints:
            self.queue.enqueue(tuple(waypoint))
        self.stack.clear()
        self.breadcrumbs.clear()
        self.current_waypoint = None
        self.active_target = None
        self.abort_reason = None
        self.drone.position = self.base_position
        self.drone.set_position(*self.base_position)
        self.drone.set_waypoint(None)
        self.state_machine.reset()
        self._completed_count = 0
        self._total_waypoints = 0
        self._waypoint_sequence = 0
        self._seed_base_checkpoint()
        self._record_event('INFO', 'Mission reset to initial condition.', {'base_position': list(self.base_position)})

    def _state_locked(self) -> dict[str, Any]:
        queue_snapshot = self.queue.to_list()
        stack_snapshot = self.stack.to_list()
        return {
            'state': self.state_machine.state.value,
            'coordinates': {'x': round(self.drone.position[0], 3), 'y': round(self.drone.position[1], 3)},
            'base': {'x': round(self.base_position[0], 3), 'y': round(self.base_position[1], 3)},
            'current_waypoint': self.current_waypoint,
            'mission_queue': [list(item) for item in queue_snapshot],
            'rollback_stack': stack_snapshot,
            'breadcrumbs': self.breadcrumbs,
            'mission_progress': {
                'completed': self._completed_count,
                'pending': self.queue.size(),
                'checkpoints_committed': max(self.stack.size() - 1, 0),
                'total_waypoints': self._total_waypoints,
            },
            'active_target': self.active_target,
            'emergency_reason': self.abort_reason,
            'latest_events': list(self.events)[-20:],
            'simulation_rate': CONFIG.update_rate_hz,
            'abort_available': self.state_machine.state in {MissionState.READY, MissionState.RUNNING, MissionState.IDLE},
            'simulation_running': self.simulation_running,
        }

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return self._state_locked()

    def reset(self) -> None:
        with self.lock:
            self.stop_event.set()
            if self.simulation_thread is not None and self.simulation_thread.is_alive():
                self.simulation_thread.join(timeout=1.0)
            self.stop_event.clear()
            self.simulation_running = False
            self._reset_state()

    def start(self) -> dict[str, Any]:
        with self.lock:
            if self.queue.is_empty():
                raise HTTPException(status_code=400, detail='Mission cannot start because no waypoints are queued.')
            if self.state_machine.state in {MissionState.RUNNING, MissionState.ABORTING, MissionState.COMPLETED, MissionState.SAFE_AT_BASE}:
                raise HTTPException(status_code=409, detail=f'Mission is already in {self.state_machine.state.value} state.')
            if self.simulation_running:
                raise HTTPException(status_code=409, detail='Simulation loop is already running.')
            if self.state_machine.state == MissionState.IDLE:
                self.state_machine.transition_to(MissionState.READY)
            self.current_waypoint = self.queue.peek() if not self.queue.is_empty() else None
            self.simulation_running = True
            self.stop_event.clear()
            self.mission_started_s = time.monotonic()
            self._record_event('INFO', 'Mission started.', {'next_waypoint': self.current_waypoint})
            self._run_background_loop()
            return self._state_locked()

    def _run_background_loop(self) -> None:
        if self.simulation_thread is not None and self.simulation_thread.is_alive():
            return
        self.simulation_thread = threading.Thread(target=self._mission_loop, daemon=True)
        self.simulation_thread.start()

    def _mission_loop(self) -> None:
        while not self.stop_event.is_set():
            time.sleep(1.0 / CONFIG.update_rate_hz)
            with self.lock:
                state = self.state_machine.state
                if state == MissionState.READY:
                    self.state_machine.transition_to(MissionState.RUNNING)
                    self.current_waypoint = self.queue.peek() if not self.queue.is_empty() else None
                    self._record_event('INFO', 'Forward mission underway.', {'next_waypoint': self.current_waypoint})
                    continue

                if state == MissionState.RUNNING:
                    if self.current_waypoint is None:
                        if self.queue.is_empty():
                            self.state_machine.transition_to(MissionState.COMPLETED)
                            self.simulation_running = False
                            self._record_event('INFO', 'Mission completed.', {'final_position': list(self.drone.position)})
                            self.stop_event.set()
                            continue
                        self.current_waypoint = self.queue.peek()
                    if self.current_waypoint is not None:
                        self.drone.set_waypoint(self.current_waypoint)
                        self.drone.step_toward_target(self.current_waypoint, 1.0 / CONFIG.update_rate_hz)
                        if self.drone.at_target(self.current_waypoint):
                            self.drone.set_position(*self.current_waypoint)
                            self._completed_count += 1
                            self._total_waypoints = max(self._total_waypoints, self._completed_count)
                            self._waypoint_sequence += 1
                            checkpoint = self._checkpoint_payload(self.current_waypoint[0], self.current_waypoint[1], self._waypoint_sequence, 'COMMITTED', f'WP-{self._waypoint_sequence}')
                            self.stack.push(checkpoint)
                            self.breadcrumbs.append({'x': self.current_waypoint[0], 'y': self.current_waypoint[1], 'sequence': self._waypoint_sequence})
                            self._record_event('INFO', 'Waypoint verified and checkpoint committed.', {'waypoint': list(self.current_waypoint), 'sequence': self._waypoint_sequence})
                            self.queue.dequeue()
                            self.current_waypoint = self.queue.peek() if not self.queue.is_empty() else None
                            if self.current_waypoint is None and self.queue.is_empty():
                                self.state_machine.transition_to(MissionState.COMPLETED)
                                self.simulation_running = False
                                self.stop_event.set()
                                self._record_event('INFO', 'Final waypoint completed.', {'final_position': list(self.drone.position)})
                            continue

                if state == MissionState.ABORTING:
                    if self.current_waypoint is not None:
                        self.current_waypoint = None
                    if self.stack.is_empty():
                        if self.drone.at_target(self.base_position):
                            self.state_machine.transition_to(MissionState.SAFE_AT_BASE)
                            self.simulation_running = False
                            self.stop_event.set()
                            self._record_event('EMERGENCY', 'Drone reached base and mission entered SAFE_AT_BASE.', {'base_position': list(self.base_position)})
                        else:
                            self.drone.step_toward_target(self.base_position, 1.0 / CONFIG.update_rate_hz)
                        continue
                    target = self.stack.peek()
                    self.active_target = target
                    self.drone.set_waypoint((target['x'], target['y']))
                    self.drone.step_toward_target((target['x'], target['y']), 1.0 / CONFIG.update_rate_hz)
                    if self.drone.at_target((target['x'], target['y'])):
                        self._record_event('WARNING', 'Rollback target reached.', {'target': target})
                        self.stack.pop()
                        self.active_target = self.stack.peek() if not self.stack.is_empty() else None
                        if self.stack.is_empty():
                            self.drone.set_waypoint(None)
                            if self.drone.at_target(self.base_position):
                                self.state_machine.transition_to(MissionState.SAFE_AT_BASE)
                                self.simulation_running = False
                                self.stop_event.set()
                                self._record_event('EMERGENCY', 'Rollback complete and drone is at base.', {'base_position': list(self.base_position)})
                        else:
                            next_target = self.stack.peek()
                            self.active_target = next_target
                            self.drone.set_waypoint((next_target['x'], next_target['y']))
                    continue

                if state in {MissionState.COMPLETED, MissionState.SAFE_AT_BASE}:
                    self.simulation_running = False
                    self.stop_event.set()
                    break

    def abort(self, reason: str) -> dict[str, Any]:
        with self.lock:
            state = self.state_machine.state
            if state in {MissionState.COMPLETED, MissionState.SAFE_AT_BASE}:
                return self._state_locked()
            if state == MissionState.ABORTING:
                return {'state': state.value, 'emergency_reason': self.abort_reason, 'status': 'already_aborting'}
            self.abort_reason = reason
            flushed = self.queue.size()
            self.queue.clear()
            self.current_waypoint = None
            self._record_event('EMERGENCY', 'Emergency accepted.', {'reason': reason, 'flushed_waypoints': flushed})
            self.state_machine.transition_to(MissionState.ABORTING)
            if self.stack.is_empty():
                if self.drone.at_target(self.base_position):
                    self.state_machine.transition_to(MissionState.SAFE_AT_BASE)
                    self._record_event('EMERGENCY', 'Emergency accepted at base; direct safe-at-base transition.', {'reason': reason})
                    self.simulation_running = False
                    self.stop_event.set()
                    return self._state_locked()
            self.active_target = self.stack.peek() if not self.stack.is_empty() else None
            if self.stack.is_empty() and self.drone.at_target(self.base_position):
                self.state_machine.transition_to(MissionState.SAFE_AT_BASE)
                self.simulation_running = False
                self.stop_event.set()
            return self._state_locked()

    def add_waypoint(self, waypoint: tuple[float, float], label: str | None = None) -> dict[str, Any]:
        with self.lock:
            state = self.state_machine.state
            if state in {MissionState.ABORTING, MissionState.COMPLETED, MissionState.SAFE_AT_BASE}:
                raise HTTPException(status_code=409, detail='New waypoints are blocked during emergency rollback or after mission completion.')
            if self.queue.size() >= CONFIG.max_waypoints:
                raise HTTPException(status_code=400, detail='Waypoint limit reached.')
            self.queue.enqueue(waypoint)
            self._record_event('INFO', 'Waypoint queued.', {'waypoint': list(waypoint), 'label': label})
            return {'status': 'queued', 'waypoint': [waypoint[0], waypoint[1]], 'queue_size': self.queue.size()}

    def events_payload(self) -> list[dict[str, Any]]:
        with self.lock:
            return list(self.events)


service = MissionService()

app = FastAPI(title='AURORA GCS', version='1.0.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

static_dir = BASE_DIR / 'app' / 'static'
app.mount('/static', StaticFiles(directory=str(static_dir)), name='static')


@app.get('/')
def home() -> FileResponse:
    return FileResponse(static_dir / 'index.html')


@app.get('/api/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


@app.get('/api/state')
def get_state() -> dict[str, Any]:
    return service.snapshot()


@app.get('/api/events')
def get_events() -> list[dict[str, Any]]:
    return service.events_payload()


@app.post('/api/start')
def start_mission() -> dict[str, Any]:
    try:
        return service.start()
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post('/api/reset')
def reset_mission() -> dict[str, Any]:
    service.reset()
    return service.snapshot()


@app.post('/api/abort')
def abort_mission(payload: AbortInput) -> dict[str, Any]:
    return service.abort(payload.reason)


@app.post('/api/waypoint/add')
def add_waypoint_route(payload: WaypointInput) -> dict[str, Any]:
    return service.add_waypoint((float(payload.x), float(payload.y)), payload.label)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=True)
