# AURORA — Autonomous UAV Deterministic Trajectory Rollback & Fail-Safe Ground Control Station

## Problem statement

AURORA is a software simulation that shows how a UAV can safely retrace a previously verified mission corridor after a simulated emergency. The project illustrates queue scheduling, stack rollback, deterministic state transitions, and backend-controlled simulation logic in a way that is intuitive for beginners while still rigorous enough for ECE technical screening.

## Motivation

The simulation is designed for students and early-career engineers who want to understand how embedded and aerospace systems preserve safe mission states under failure conditions. The emphasis is on deterministic behavior, safe rollback, and clear engineering documentation rather than certification or real-world flight claims.

## Functional overview

- Custom FIFO queue for mission waypoints.
- Custom LIFO stack for verified checkpoints.
- Deterministic backend state machine.
- Browser-based radar and telemetry dashboard.
- Emergency handling and rollback in reverse order.
- Automated `pytest` suite for data structures, APIs, and concurrency.

## Local setup

1. Install Python 3.11+.
2. Create a virtual environment:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Start the API and frontend:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

5. Open `http://localhost:8000` in a browser.

6. Run tests:

```powershell
pytest -q
```

## Deployment

Use Render or Railway with a Python web service and the command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Scope and limitations

This project is a software simulation and does not claim real-world collision avoidance, flight qualification, or hard real-time guarantees.
