# AURORA Architecture

AURORA separates the authoritative mission logic from the frontend dashboard.

## Main modules

- `app/structures.py` — linked-list queue and stack.
- `app/state_machine.py` — finite-state sequencing and validation.
- `app/drone.py` — motion interpolation and position math.
- `app/main.py` — FastAPI API and runtime controller.
- `app/static/` — HTML, CSS, and JavaScript dashboard.

## State flow

```text
IDLE -> READY -> RUNNING -> COMPLETED
                   \-> ABORTING -> SAFE_AT_BASE
READY -> ABORTING
```

## Notes

The backend serializes state transitions with a re-entrant lock so aborts, state updates, and queue changes cannot conflict.
