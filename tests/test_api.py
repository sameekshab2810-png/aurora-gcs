from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_state_endpoint():
    response = client.get('/api/state')
    assert response.status_code == 200
    body = response.json()
    assert 'state' in body
    assert 'coordinates' in body


def test_start_and_abort_endpoints():
    reset = client.post('/api/reset')
    assert reset.status_code == 200
    start = client.post('/api/start')
    assert start.status_code == 200
    abort = client.post('/api/abort', json={'reason': 'Sensor saturation'})
    assert abort.status_code == 200


def test_waypoint_addition_invalid_coordinates():
    response = client.post('/api/waypoint/add', json={'x': 5000, 'y': 10})
    assert response.status_code == 422
