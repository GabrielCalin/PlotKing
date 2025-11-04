# ui/handlers.py
import gradio as gr
import os, re, json
from pipeline.constants import RUN_MODE_CHOICES
from pipeline.state_manager import request_stop, get_checkpoint, clear_stop, clear_checkpoint, save_checkpoint
from utils.timestamp import ts_prefix

# --- Helpers “pure” folosite în mai multe locuri ---

def choose_plot_for_pipeline(plot, refined):
    return refined if (refined or "").strip() else plot

def pre_run_reset_and_controls():
    clear_stop()
    clear_checkpoint()
    return (
        gr.update(visible=True, interactive=True, value="🛑 Stop"),
        gr.update(visible=False),  # resume
        gr.update(visible=False),  # generate
        gr.update(visible=False),  # regen expanded
        gr.update(visible=False),  # regen overview
        gr.update(visible=False),  # regen chapter
    )

def post_pipeline_controls():
    checkpoint = get_checkpoint()
    if not checkpoint:
        return (
            gr.update(interactive=True, visible=False),  # stop
            gr.update(visible=False),  # resume
            gr.update(visible=True),  # generate
            gr.update(visible=False), # regen expanded
            gr.update(visible=False), # regen overview
            gr.update(visible=False), # regen chapter
        )

    expanded_visible = bool(checkpoint.get("expanded_plot"))
    overview_visible = bool(checkpoint.get("chapters_overview"))
    chapters_count = len(checkpoint.get("chapters_full", []))

    try:
        total_chapters = int(checkpoint.get("num_chapters") or chapters_count)
    except Exception:
        total_chapters = chapters_count

    has_resume_markers = bool(checkpoint.get("pending_validation_index")) or bool(checkpoint.get("next_chapter_index"))
    is_full_complete = expanded_visible and overview_visible and (chapters_count >= max(1, total_chapters)) and not has_resume_markers
    stopped_at_overview = expanded_visible and overview_visible and (chapters_count == 0) and not has_resume_markers
    chapters_visible = chapters_count > 0

    if is_full_complete:
        return (
            gr.update(interactive=True, visible=False),  # stop
            gr.update(visible=False),  # resume
            gr.update(visible=True),   # generate
            gr.update(visible=expanded_visible),
            gr.update(visible=overview_visible),
            gr.update(visible=chapters_visible),
        )
    elif stopped_at_overview:
        return (
            gr.update(interactive=True, visible=False),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=expanded_visible),
            gr.update(visible=overview_visible),
            gr.update(visible=False),
        )
    else:
        return (
            gr.update(interactive=True, visible=False),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=expanded_visible),
            gr.update(visible=overview_visible),
            gr.update(visible=chapters_visible),
        )

def show_stop_only():
    return (
        gr.update(visible=True, interactive=True, value="🛑 Stop"),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )

def stop_pipeline(cur_status):
    request_stop()
    new_status = (cur_status + "\n" + ts_prefix("🛑 Stop requested")).strip() if cur_status else ts_prefix("🛑 Stop requested")
    return new_status, gr.update(interactive=False, value="Stopping…"), gr.update(visible=False)

def show_controls_on_resume_run():
    return (
        gr.update(visible=True, interactive=True, value="🛑 Stop"),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )

# generator; pass-through la pipeline_fn primit din interface
def resume_pipeline(pipeline_fn):
    checkpoint = get_checkpoint()
    if not checkpoint:
        yield "", "", [], "", gr.update(choices=[]), "_No checkpoint_", "⚠️ No checkpoint found to resume from.", ""
        return
    plot = checkpoint.get("plot", "")
    num_chapters = checkpoint.get("num_chapters", 0)
    genre = checkpoint.get("genre", "")
    anpc = checkpoint.get("anpc", 0)
    rm = checkpoint.get("run_mode", RUN_MODE_CHOICES["FULL"])

    expanded_visible = bool(checkpoint.get("expanded_plot"))
    overview_visible = bool(checkpoint.get("chapters_overview"))
    chapters_count = len(checkpoint.get("chapters_full", []))
    has_resume_markers = bool(checkpoint.get("pending_validation_index")) or bool(checkpoint.get("next_chapter_index"))
    stopped_at_overview = expanded_visible and overview_visible and (chapters_count == 0) and not has_resume_markers and (rm == RUN_MODE_CHOICES.get("OVERVIEW"))

    resume_run_mode = RUN_MODE_CHOICES["FULL"] if stopped_at_overview else rm

    clear_stop()
    clear_checkpoint()
    yield from pipeline_fn(plot, num_chapters, genre, anpc, resume_run_mode, checkpoint=checkpoint)

def refresh_expanded(pipeline_fn):
    checkpoint = get_checkpoint()
    if not checkpoint:
        yield "", "", [], "", gr.update(), "_No checkpoint_", "⚠️ Cannot refresh without checkpoint.", ""
        return
    clear_stop()
    yield from pipeline_fn(
        checkpoint["plot"],
        checkpoint["num_chapters"],
        checkpoint["genre"],
        checkpoint["anpc"],
        checkpoint["run_mode"],
        checkpoint=checkpoint,
        refresh_from="expanded"
    )

def refresh_overview(pipeline_fn):
    checkpoint = get_checkpoint()
    if not checkpoint:
        yield "", "", [], "", gr.update(), "_No checkpoint_", "⚠️ Cannot refresh without checkpoint.", ""
        return
    clear_stop()
    yield from pipeline_fn(
        checkpoint["plot"],
        checkpoint["num_chapters"],
        checkpoint["genre"],
        checkpoint["anpc"],
        checkpoint["run_mode"],
        checkpoint=checkpoint,
        refresh_from="overview"
    )

def refresh_chapter(pipeline_fn, selected_name):
    checkpoint = get_checkpoint()
    if not checkpoint:
        yield "", "", [], "", gr.update(), "_No checkpoint_", "⚠️ Cannot refresh without checkpoint.", ""
        return
    if not selected_name:
        yield "", "", [], "", gr.update(), "_No chapter selected_", "⚠️ Please select a chapter.", ""
        return
    try:
        idx = int(selected_name.split(" ")[1])
    except Exception:
        idx = None
    clear_stop()
    if idx == 1:
        current_text_update = ""
        dropdown_update = gr.update(value=None)
    else:
        current_text_update = checkpoint.get("chapters_full", [])[0] if checkpoint.get("chapters_full") else ""
        dropdown_update = gr.update(value="Chapter 1")

    yield (
        gr.update(value=checkpoint.get("expanded_plot", "")),
        gr.update(value=checkpoint.get("chapters_overview", "")),
        checkpoint.get("chapters_full", []),
        current_text_update,
        dropdown_update,
        f"Refreshing from chapter {idx}...",
        ts_prefix(f"🔁 Refresh from chapter {idx} initiated."),
        checkpoint.get("validation_text", ""),
    )
    yield from pipeline_fn(
        checkpoint["plot"],
        checkpoint["num_chapters"],
        checkpoint["genre"],
        checkpoint["anpc"],
        checkpoint["run_mode"],
        checkpoint=checkpoint,
        refresh_from=idx
    )

# plot/refine mode toggles
def show_original(plot, refined):
    return gr.update(value=plot, label="Original", interactive=True,
                     placeholder="Ex: A young girl discovers a portal to another world..."), \
           "original", gr.update(value="🪄")

def show_refined(plot, refined):
    return gr.update(value=refined, label="Refined", interactive=False,
                     placeholder="This refined version will be used for generation (if present)."), \
           "refined", gr.update(value="🧹")

def refine_or_clear(plot, refined, mode, genre, refine_fn):
    if mode == "refined":
        return gr.update(value=plot, label="Original", interactive=True), "", "original", gr.update(value="🪄")
    else:
        new_refined = refine_fn(plot, genre)
        return gr.update(value=new_refined, label="Refined", interactive=False,
                         placeholder="This refined version will be used for generation (if present)."), \
               new_refined, "refined", gr.update(value="🧹")

def sync_textbox(text, mode):
    if mode == "refined":
        return gr.update(), text
    else:
        return text, gr.update()

# ==== Project Management (save / load / delete) ====

import os, re, json
from pipeline.state_manager import save_checkpoint
from utils.timestamp import ts_prefix
from pipeline.constants import RUN_MODE_CHOICES
import gradio as gr

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


def save_project(project_name,
                 plot_input, genre_input, chapters_input, anpc_input,
                 expanded_output, chapters_overview_output, chapters_state):
    _ensure_projects_dir()
    err = _validate_name(project_name)
    if err:
        return ts_prefix(err), gr.update(choices=list_projects(), value=None)

    try:
        num_chapters = int(chapters_input) if chapters_input is not None else None
    except Exception:
        num_chapters = None
    try:
        anpc = int(anpc_input) if anpc_input is not None else None
    except Exception:
        anpc = None

    checkpoint = get_checkpoint() or {}
    data = {
        "project_name": project_name.strip(),
        "plot_original": checkpoint.get("plot", plot_input or ""),
        "plot_refined": checkpoint.get("refined_plot", ""),
        "genre": (genre_input or ""),
        "num_chapters": num_chapters,
        "avg_pages_per_chapter": anpc,
        "expanded_plot": (expanded_output or ""),
        "chapters_overview": (chapters_overview_output or ""),
        "chapters": chapters_state or [],
    }

    path = _project_path(project_name.strip())
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return ts_prefix(f"❌ Save failed: {e}"), gr.update(choices=list_projects())

    projects = list_projects()
    msg = ts_prefix(f"💾 Saved project “{project_name.strip()}”.")
    return msg, gr.update(choices=projects, value=project_name.strip())


def load_project(selected_name, current_status):
    if not selected_name:
        msg = ts_prefix("❌ Select a project to load.")
        return (gr.update(), gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(), gr.update(), gr.update(),
                gr.update(), gr.update(), gr.update(), current_status + "\n" + msg)

    path = _project_path(selected_name)
    if not os.path.exists(path):
        msg = ts_prefix(f"❌ Project “{selected_name}” not found.")
        return (gr.update(),)*11 + (current_status + "\n" + msg,)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        msg = ts_prefix(f"❌ Failed to read project: {e}")
        return (gr.update(),)*11 + (current_status + "\n" + msg,)

    plot = data.get("plot_original", "")
    refined = data.get("plot_refined", "")
    genre = data.get("genre", "")
    num_chapters = data.get("num_chapters", None)
    anpc = data.get("avg_pages_per_chapter", None)
    expanded = data.get("expanded_plot", "")
    overview = data.get("chapters_overview", "")
    chapters_list = data.get("chapters", []) or []

    checkpoint = {
        "plot": plot,
        "refined_plot": refined,
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

    # Capitol handling
    if not chapters_list:
        chapter_dropdown = gr.update(choices=[], value=None)
        current_chapter_text = gr.update(value="", visible=False)
        chapter_counter = "_No chapters yet_"
    else:
        chapter_dropdown = gr.update(choices=[f"Chapter {i+1}" for i in range(len(chapters_list))],
                                     value="Chapter 1")
        current_chapter_text = gr.update(value=chapters_list[0], visible=True)
        chapter_counter = f"Chapter 1 / {len(chapters_list)}"

    msg = ts_prefix(f"📂 Loaded project “{selected_name}”.")
    return (
        gr.update(value=plot),              # plot_input
        gr.update(value=genre),             # genre_input
        gr.update(value=num_chapters),      # chapters_input
        gr.update(value=anpc),              # anpc_input
        gr.update(value=expanded),          # expanded_output
        gr.update(value=overview),          # chapters_output
        chapters_list,                      # chapters_state
        gr.update(value=selected_name),     # project_name
        chapter_dropdown,                   # chapter_selector
        current_chapter_text,               # current_chapter_output
        gr.update(value=chapter_counter),   # chapter_counter
        current_status + "\n" + msg         # status_output
    )


def delete_project(selected_name):
    if not selected_name:
        return ts_prefix("❌ Select a project to delete."), gr.update(choices=list_projects(), value=None)

    path = _project_path(selected_name)
    if not os.path.exists(path):
        return ts_prefix(f"❌ Project “{selected_name}” not found."), gr.update(choices=list_projects(), value=None)

    try:
        os.remove(path)
    except Exception as e:
        return ts_prefix(f"❌ Delete failed: {e}"), gr.update(choices=list_projects(), value=None)

    projects = list_projects()
    new_value = projects[0] if projects else None
    return ts_prefix(f"🗑️ Deleted project “{selected_name}”."), gr.update(choices=projects, value=new_value)
