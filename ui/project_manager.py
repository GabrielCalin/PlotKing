# ui/project_manager.py

import os, re, json
import gradio as gr
from utils.timestamp import ts_prefix
from pipeline.constants import RUN_MODE_CHOICES
from pipeline.state_manager import save_checkpoint, clear_stop, clear_checkpoint

# === Config & helpers ===
_PROJECTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "projects")
_NAME_RE = re.compile(r'^[A-Za-z0-9 _-]+$')

def _ensure_projects_dir():
    os.makedirs(_PROJECTS_DIR, exist_ok=True)

def _project_path(name: str) -> str:
    return os.path.join(_PROJECTS_DIR, f"{name}.json")

def _validate_name(name: str):
    if not name or not name.strip():
        return "❌ Please enter a project name."
    name = name.strip()
    if not _NAME_RE.match(name):
        return "❌ Invalid project name. Use letters, numbers, spaces, '-' or '_' only."
    return None

def list_projects():
    _ensure_projects_dir()
    names = [fn[:-5] for fn in os.listdir(_PROJECTS_DIR) if fn.lower().endswith(".json")]
    names.sort(key=lambda s: s.lower())
    return names

# helper local (evităm import circular din handlers)
def _choose_plot_for_pipeline(plot, refined):
    return refined if (refined or "").strip() else plot

# === Actions ===

def save_project(
    project_name,
    genre_input, chapters_input, anpc_input,
    plot_state_value, refined_plot_state_value,
    current_status
):
    _ensure_projects_dir()

    err = _validate_name(project_name)
    if err:
        return current_status + "\n" + ts_prefix(err), gr.update(choices=list_projects(), value=None)

    # Procesează parametrii
    try:
        num_chapters = int(chapters_input) if chapters_input is not None else None
    except Exception:
        num_chapters = None
    try:
        anpc = int(anpc_input) if anpc_input is not None else None
    except Exception:
        anpc = None
    genre = genre_input or ""

    # Checkpoint-ul este sursa de adevăr pentru expanded_plot, chapters_overview și chapters
    from pipeline.state_manager import get_checkpoint
    checkpoint = get_checkpoint()
    
    if checkpoint:
        # Citește din checkpoint doar expanded_plot, chapters_overview și chapters
        expanded_plot = checkpoint.get("expanded_plot") or ""
        chapters_overview = checkpoint.get("chapters_overview") or ""
        chapters = checkpoint.get("chapters_full") or []
    else:
        # Dacă checkpoint nu există, folosește valori goale
        expanded_plot = ""
        chapters_overview = ""
        chapters = []

    data = {
        "project_name": project_name.strip(),
        "plot_original": plot_state_value or "",
        "plot_refined": refined_plot_state_value or "",
        "genre": genre,
        "num_chapters": num_chapters,
        "avg_pages_per_chapter": anpc,
        "expanded_plot": expanded_plot,
        "chapters_overview": chapters_overview,
        "chapters": chapters,
    }

    path = _project_path(project_name.strip())
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return current_status + "\n" + ts_prefix(f"❌ Save failed: {e}"), gr.update(choices=list_projects())

    projects = list_projects()
    msg = ts_prefix(f"💾 Saved project “{project_name.strip()}”.")
    return current_status + "\n" + msg, gr.update(choices=projects, value=project_name.strip())

def load_project(selected_name, current_status):
    if not selected_name:
        msg = ts_prefix("❌ Select a project to load.")
        return (gr.update(), gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(), gr.update(),
                current_status + "\n" + msg)

    path = _project_path(selected_name)
    if not os.path.exists(path):
        msg = ts_prefix(f"❌ Project “{selected_name}” not found.")
        return (gr.update(),)*14 + (current_status + "\n" + msg,)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        msg = ts_prefix(f"❌ Failed to read project: {e}")
        return (gr.update(),)*14 + (current_status + "\n" + msg,)

    plot_original = data.get("plot_original", "")
    plot_refined = data.get("plot_refined", "")
    chosen_plot = _choose_plot_for_pipeline(plot_original, plot_refined)
    genre = data.get("genre", "")
    num_chapters = data.get("num_chapters", None)
    anpc = data.get("avg_pages_per_chapter", None)
    expanded = data.get("expanded_plot", "")
    overview = data.get("chapters_overview", "")
    chapters_list = data.get("chapters", []) or []

    checkpoint = {
        "plot": chosen_plot,
        "num_chapters": num_chapters,
        "genre": genre,
        "anpc": anpc,
        "run_mode": RUN_MODE_CHOICES["FULL"],
        "expanded_plot": expanded,
        "chapters_overview": overview,
        "chapters_full": chapters_list,
        "validation_text": "",
        "overview_validated": bool(overview),
        "pending_validation_index": None,
        "next_chapter_index": None,
        "status_log": [ts_prefix(f"📂 Project “{selected_name}” loaded.")],
    }
    save_checkpoint(checkpoint)

    if not chapters_list:
        chapter_dropdown = gr.update(choices=[], value=None)
        current_chapter_text = gr.update(value="")
        chapter_counter = "_No chapters yet_"
    else:
        chapter_dropdown = gr.update(
            choices=[f"Chapter {i+1}" for i in range(len(chapters_list))],
            value="Chapter 1"
        )
        current_chapter_text = gr.update(value=chapters_list[0])
        chapter_counter = ""

    if plot_refined and plot_refined.strip():
        plot_display = gr.update(value=plot_refined, interactive=False, label="Refined")
        refine_btn_state = gr.update(value="🧹")
        mode_value = "refined"
    else:
        plot_display = gr.update(value=plot_original, interactive=True, label="Original")
        refine_btn_state = gr.update(value="🪄")
        mode_value = "original"

    msg = ts_prefix(f"📂 Loaded project “{selected_name}”.")

    # --- Determine visibility for control buttons ---
    expanded_visible = bool(expanded and expanded.strip())
    overview_visible = bool(overview and overview.strip())
    chapters_visible = len(chapters_list) > 0

    total_chapters = num_chapters or len(chapters_list)
    incomplete = expanded_visible and (not overview_visible or len(chapters_list) < total_chapters)

    # Resume logic
    resume_visible = incomplete
    stop_visible = False
    generate_visible = True

    return (
        plot_display,
        gr.update(value=genre),
        gr.update(value=num_chapters),
        gr.update(value=anpc),
        gr.update(value=expanded),
        gr.update(value=overview),
        chapters_list,
        gr.update(value=selected_name),
        chapter_dropdown,
        current_chapter_text,
        gr.update(value=chapter_counter),
        plot_original,        # State: ORIGINAL
        plot_refined,         # State: REFINED
        mode_value,           # current_mode
        refine_btn_state,
        current_status + "\n" + msg,
        # --- control visibility updates ---
        gr.update(visible=stop_visible, interactive=False, value="🛑 Stop"),
        gr.update(visible=resume_visible, interactive=True, value="▶️ Resume"),
        gr.update(visible=generate_visible, interactive=True, value="🚀 Generate Book"),
        gr.update(visible=expanded_visible),   # regenerate_expanded_btn
        gr.update(visible=overview_visible),   # regenerate_overview_btn
        gr.update(visible=chapters_visible),   # regenerate_chapter_btn
    )

def delete_project(selected_name, current_status):
    if not selected_name:
        return current_status + "\n" + ts_prefix("❌ Select a project to delete."), gr.update(choices=list_projects(), value=None)

    path = _project_path(selected_name)
    if not os.path.exists(path):
        return current_status + "\n" + ts_prefix(f"❌ Project “{selected_name}” not found."), gr.update(choices=list_projects(), value=None)

    try:
        os.remove(path)
    except Exception as e:
        return current_status + "\n" + ts_prefix(f"❌ Delete failed: {e}"), gr.update(choices=list_projects(), value=None)

    projects = list_projects()
    new_value = projects[0] if projects else None
    return current_status + "\n" + ts_prefix(f"🗑️ Deleted project “{selected_name}”."), gr.update(choices=projects, value=new_value)

def new_project(current_status):
    """
    Resetează complet toate inputurile și outputurile – echivalent cu o sesiune nouă.
    Toate butoanele sunt resetate: doar Generate rămâne vizibil.
    """
    clear_stop()
    clear_checkpoint()

    new_log = (current_status or "") + "\n" + ts_prefix("🆕 New project started.")

    return (
        gr.update(value="", label="Original", interactive=True),   # plot_input
        gr.update(value=""),                                       # genre_input
        gr.update(value=5),                                        # num_chapters
        gr.update(value=5),                                        # anpc_input
        gr.update(value=""),                                       # expanded_output
        gr.update(value=""),                                       # chapters_output
        [],                                                        # chapters_state
        gr.update(value=""),                                       # project_name
        gr.update(choices=[], value=None),                         # chapter_selector
        gr.update(value="", visible=True),                         # current_chapter_output (vizibil, gol)
        "_No chapters yet_",                                       # chapter_counter
        gr.update(value=""),                                       # plot_state (original)
        gr.update(value=""),                                       # refined_plot_state
        gr.update(value="🪄"),                                     # refine_btn reset
        new_log,                                                   # status_output (append)
        gr.update(visible=False),                                  # regenerate_expanded_btn
        gr.update(visible=False),                                  # regenerate_overview_btn
        gr.update(visible=False),                                  # regenerate_chapter_btn
        gr.update(visible=False, interactive=False, value="🛑 Stop"),   # stop_btn
        gr.update(visible=False, interactive=False, value="▶️ Resume"), # resume_btn
        gr.update(visible=True, interactive=True, value="🚀 Generate Book"), # generate_btn
    )
