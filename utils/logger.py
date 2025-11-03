from utils.timestamp import ts_prefix

def log_ui(status_list: list, msg: str) -> None:
    status_list.append(ts_prefix(msg))

def log_console(msg: str) -> None:
    print(ts_prefix(msg), flush=True)
