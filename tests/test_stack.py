from app.structures import MissionStack


def test_empty_stack():
    stack = MissionStack[int]()
    assert stack.is_empty()
    assert stack.size() == 0
    assert stack.to_list() == []


def test_push_pop_order():
    stack = MissionStack[int]()
    for value in [1, 2, 3]:
        stack.push(value)
    assert stack.peek() == 3
    assert stack.pop() == 3
    assert stack.peek() == 2


def test_clear_and_reuse():
    stack = MissionStack[int]()
    stack.push(4)
    stack.push(5)
    stack.clear()
    assert stack.is_empty()
    stack.push(8)
    assert stack.pop() == 8


def test_large_history():
    stack = MissionStack[int]()
    for value in range(100):
        stack.push(value)
    assert stack.size() == 100
    assert stack.peek() == 99
