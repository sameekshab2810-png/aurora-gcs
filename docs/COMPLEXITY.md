# Complexity analysis

## Queue

- Enqueue: O(1)
- Dequeue: O(1)
- Peek: O(1)
- Clear: O(1)
- Size: O(1)
- to_list: O(n)

## Stack

- Push: O(1)
- Pop: O(1)
- Peek: O(1)
- Clear: O(1)
- Size: O(1)
- to_list: O(n)

## Mission operations

- Forward waypoint dispatch: O(1) per update cycle.
- Checkpoint recording: O(1)
- Rollback step: O(1)
- Emergency queue flush: O(1) by detaching the linked list head and tail.

The algorithmic costs are deterministic; Python allocation and garbage collection still impose practical overhead but remain acceptable for this simulation scale.
