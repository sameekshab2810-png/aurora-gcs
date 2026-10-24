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

### Quick deploy to Render

1. Open the [AURORA Render deployment page](https://render.com/deploy?repo=https://github.com/sameekshab2810-png/aurora-gcs).
2. Sign in to Render (or create an account), review the service settings, then select **Deploy Blueprint**.
3. Wait for Render to finish building and starting the service. Copy the generated `onrender.com` URL and open it to show the website.
4. Check that `<your-service-url>/api/health` returns `{"status":"ok"}`.

The included `render.yaml` installs `requirements.txt`, starts Uvicorn on Render's `PORT`, and configures `/api/health` as the health check. Render account authorization and the final public URL must be completed by the account owner; no deployed URL is claimed here.

Free hosting may sleep when idle and can take a short time to wake up. Allow the service to finish its first build before presenting.

### Other Python hosts

Use Render or Railway with a Python web service and the command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Scope and limitations

This project is a software simulation and does not claim real-world collision avoidance, flight qualification, or hard real-time guarantees.
