from datetime import datetime
def ts_prefix(msg: str) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return f"[{ts}] {msg}"
