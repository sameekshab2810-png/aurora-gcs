# Viva guide

- Explain why queue ordering matters for waypoint dispatch.
- Show how the stack lets the drone reverse through verified checkpoints.
- Describe how a single backend lock prevents contradictory state changes.
- Explain why route history remains visible even as rollback pops the active checkpoint target.
