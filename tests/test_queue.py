from app.structures import MissionQueue


def test_empty_queue():
    q = MissionQueue[int]()
    assert q.is_empty()
    assert q.size() == 0
    assert q.to_list() == []


def test_single_enqueue_dequeue():
    q = MissionQueue[int]()
    q.enqueue(5)
    assert q.peek() == 5
    assert q.dequeue() == 5
    assert q.is_empty()


def test_fifo_behavior():
    q = MissionQueue[int]()
    for value in [1, 2, 3, 4]:
        q.enqueue(value)
    assert q.to_list() == [1, 2, 3, 4]
    assert q.dequeue() == 1
    assert q.dequeue() == 2
    assert q.peek() == 3


def test_clear_and_reuse():
    q = MissionQueue[int]()
    q.enqueue(10)
    q.enqueue(20)
    q.clear()
    assert q.is_empty()
    q.enqueue(99)
    assert q.dequeue() == 99


def test_large_input():
    q = MissionQueue[int]()
    values = list(range(200))
    for value in values:
        q.enqueue(value)
    assert q.size() == 200
    assert q.dequeue() == 0
    assert q.peek() == 1
