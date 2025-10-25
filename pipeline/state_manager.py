from threading import Lock

_pipeline_state = {
    "stop_requested": False,
    "paused": False,
    "last_checkpoint": None,  # conține datele de reluare
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

def save_checkpoint(data):
    with _lock:
        _pipeline_state["last_checkpoint"] = data

def get_checkpoint():
    with _lock:
        return _pipeline_state["last_checkpoint"]

def clear_checkpoint():
    with _lock:
        _pipeline_state["last_checkpoint"] = None
