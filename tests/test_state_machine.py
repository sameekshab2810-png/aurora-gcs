from app.state_machine import MissionState, MissionStateMachine


def test_valid_transitions():
    machine = MissionStateMachine()
    machine.transition_to(MissionState.READY)
    machine.transition_to(MissionState.RUNNING)
    assert machine.state == MissionState.RUNNING


def test_invalid_transition_raises():
    machine = MissionStateMachine()
    try:
        machine.transition_to(MissionState.RUNNING)
        assert False, 'Invalid transition should raise.'
    except ValueError:
        pass


def test_abort_from_ready_and_takeoff():
    machine = MissionStateMachine(MissionState.READY)
    machine.transition_to(MissionState.ABORTING)
    assert machine.state == MissionState.ABORTING


def test_final_safe_transition():
    machine = MissionStateMachine(MissionState.ABORTING)
    machine.transition_to(MissionState.SAFE_AT_BASE)
    assert machine.state == MissionState.SAFE_AT_BASE
