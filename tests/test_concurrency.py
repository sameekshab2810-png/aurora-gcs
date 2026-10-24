import threading

from app.main import service


def test_start_abort_race_is_serialized():
    service.reset()
    results = []

    def do_start():
        try:
            results.append(service.start())
        except Exception as exc:  # pragma: no cover
            results.append({'error': str(exc)})

    def do_abort():
        try:
            results.append(service.abort('Simulated lost link'))
        except Exception as exc:  # pragma: no cover
            results.append({'error': str(exc)})

    thread_one = threading.Thread(target=do_start)
    thread_two = threading.Thread(target=do_abort)
    thread_one.start()
    thread_two.start()
    thread_one.join()
    thread_two.join()
    assert len(results) == 2
    service.reset()
