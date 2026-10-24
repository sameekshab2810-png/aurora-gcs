from __future__ import annotations

from enum import Enum


class MissionState(str, Enum):
    IDLE = 'IDLE'
    READY = 'READY'
    RUNNING = 'RUNNING'
    ABORTING = 'ABORTING'
    COMPLETED = 'COMPLETED'
    SAFE_AT_BASE = 'SAFE_AT_BASE'


class MissionStateMachine:
    """Single authoritative backend state machine for the mission lifecycle."""

    VALID_TRANSITIONS = {
        MissionState.IDLE: {MissionState.READY},
        MissionState.READY: {MissionState.RUNNING, MissionState.ABORTING},
        MissionState.RUNNING: {MissionState.COMPLETED, MissionState.ABORTING},
        MissionState.ABORTING: {MissionState.SAFE_AT_BASE},
        MissionState.COMPLETED: set(),
        MissionState.SAFE_AT_BASE: set(),
    }

    def __init__(self, initial_state: MissionState = MissionState.IDLE):
        self._state = initial_state
        self.transition_log: list[tuple[MissionState, MissionState]] = []

    @property
    def state(self) -> MissionState:
        return self._state

    def can_transition(self, from_state: MissionState, to_state: MissionState) -> bool:
        return to_state in self.VALID_TRANSITIONS.get(from_state, set())

    def transition_to(self, new_state: MissionState) -> MissionState:
        if not self.can_transition(self._state, new_state):
            raise ValueError(f'Invalid transition from {self._state.value} to {new_state.value}')
        self.transition_log.append((self._state, new_state))
        self._state = new_state
        return self._state

    def reset(self) -> None:
        self._state = MissionState.IDLE
        self.transition_log.clear()
