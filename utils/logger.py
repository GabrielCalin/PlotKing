from utils.timestamp import ts_prefix

def log_ui(status_list: list, msg: str) -> None:
    status_list.append(ts_prefix(msg))

def log_console(msg: str) -> None:
    print(ts_prefix(msg), flush=True)

def merge_logs(base_log: str, new_log_text: str) -> str:
    """
    Combină log-urile existente cu log-urile noi, evitând duplicatele.
    
    Args:
        base_log: Log-urile existente (string cu newline-uri)
        new_log_text: Log-urile noi din pipeline (string cu newline-uri)
    
    Returns:
        String combinat cu toate log-urile, fără duplicate și fără linii goale
    """
    combined_lines = base_log.split("\n") if base_log else []
    combined_lines = [line for line in combined_lines if line.strip()]
    
    if new_log_text:
        new_lines = new_log_text.split("\n")
        new_lines = [line for line in new_lines if line.strip()]
        for line in new_lines:
            if line not in combined_lines:
                combined_lines.append(line)
    
    return "\n".join(combined_lines)