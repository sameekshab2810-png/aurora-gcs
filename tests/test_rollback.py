from app.structures import MissionStack


def test_rollback_order_for_base_a_b_c():
    stack = MissionStack[dict]()
    points = [
        {'x': 0.0, 'y': 0.0, 'label': 'BASE'},
        {'x': 10.0, 'y': 10.0, 'label': 'A'},
        {'x': 20.0, 'y': 20.0, 'label': 'B'},
        {'x': 30.0, 'y': 30.0, 'label': 'C'},
    ]
    for point in points:
        stack.push(point)

    sequence = []
    while not stack.is_empty():
        sequence.append(stack.pop()['label'])

    assert sequence == ['C', 'B', 'A', 'BASE']
