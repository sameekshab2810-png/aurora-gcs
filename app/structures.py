from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar('T')


class MissionQueue(Generic[T]):
    """Custom FIFO queue implemented with a singly linked list.

    This structure keeps O(1) enqueue and dequeue while preserving insertion order.
    Clearing the queue is O(1) by detaching the linked list head and tail.
    """

    class _Node(Generic[T]):
        __slots__ = ('value', 'next')

        def __init__(self, value: T, next_node: '_Node[T] | None' = None):
            self.value = value
            self.next = next_node

    def __init__(self):
        self.head: MissionQueue._Node[T] | None = None
        self.tail: MissionQueue._Node[T] | None = None
        self._size = 0

    def enqueue(self, item: T) -> None:
        node = self._Node(item)
        if self.tail is None:
            self.head = node
            self.tail = node
        else:
            self.tail.next = node
            self.tail = node
        self._size += 1

    def dequeue(self) -> T:
        if self.head is None:
            raise IndexError('Queue is empty.')
        value = self.head.value
        self.head = self.head.next
        if self.head is None:
            self.tail = None
        self._size -= 1
        return value

    def peek(self) -> T:
        if self.head is None:
            raise IndexError('Queue is empty.')
        return self.head.value

    def clear(self) -> None:
        self.head = None
        self.tail = None
        self._size = 0

    def is_empty(self) -> bool:
        return self.head is None

    def size(self) -> int:
        return self._size

    def to_list(self) -> list[T]:
        values: list[T] = []
        current = self.head
        while current is not None:
            values.append(current.value)
            current = current.next
        return values


class MissionStack(Generic[T]):
    """Custom LIFO stack implemented with a singly linked list.

    Push and pop are O(1). The stack head is detached during clear, allowing a direct O(1)
    reset while leaving Python garbage collection to reclaim unreachable nodes.
    """

    class _Node(Generic[T]):
        __slots__ = ('value', 'next')

        def __init__(self, value: T, next_node: '_Node[T] | None' = None):
            self.value = value
            self.next = next_node

    def __init__(self):
        self.head: MissionStack._Node[T] | None = None
        self._size = 0

    def push(self, item: T) -> None:
        self.head = self._Node(item, self.head)
        self._size += 1

    def pop(self) -> T:
        if self.head is None:
            raise IndexError('Stack is empty.')
        value = self.head.value
        self.head = self.head.next
        self._size -= 1
        return value

    def peek(self) -> T:
        if self.head is None:
            raise IndexError('Stack is empty.')
        return self.head.value

    def clear(self) -> None:
        self.head = None
        self._size = 0

    def is_empty(self) -> bool:
        return self.head is None

    def size(self) -> int:
        return self._size

    def to_list(self) -> list[T]:
        values: list[T] = []
        current = self.head
        while current is not None:
            values.append(current.value)
            current = current.next
        return values
