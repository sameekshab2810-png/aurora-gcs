# API reference

## GET /api/state
Returns the current mission state and all UI-relevant telemetry.

## POST /api/start
Starts the mission if the simulation is in the proper state.

## POST /api/abort
Accepts an emergency reason and begins rollback.

## POST /api/reset
Clears the queue and resets the stack, route history, and state.

## POST /api/waypoint/add
Queues a new waypoint with coordinate validation.

## GET /api/health
Used for deployment health checks.
