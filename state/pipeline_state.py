from threading import Lock

_pipeline_state = {
    "stop_requested": False,
    "paused": False,
}
_lock = Lock()

def request_stop():
    with _lock:
        _pipeline_state["stop_requested"] = True

def clear_stop():
    with _lock:
        _pipeline_state["stop_requested"] = False

def is_stop_requested():
    with _lock:
        return _pipeline_state["stop_requested"]
