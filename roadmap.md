# 🗺️ AI Story Generator — Roadmap

This document outlines the planned development milestones for the **AI Story Generator** project, in order of implementation priority.

---

## ✅ Phase 1 — Core Validation System

1. **QOL updates**  
   - Update main documentation.
   - Fix missing content in chapter output.
   - Remove Chapter x prefix in chapter output.
   - Remove newline in validation feedback for first line and change order with process log.
   - Fix chapter writer to always receive the full text of previous chapters.

---

## 🧭 Phase 2 — User Experience Enhancements

2. **Book Genre Selection in UI**  
   - Add a genre input in the user interface.  
   - The chosen genre will influence plot generation and writing style of chapters.

3. **Export to EPUB**  
   - Allow users to export the final story as an `.epub` file, including cover and metadata.

4. **Prompt Optimization**  
   - Refine prompts used in each generation stage (plot expansion, chapter generation, validation) for higher quality and coherence.

5. **Saving Project State**  
   - Implement project state saving functionality to allow users to save and resume their work.  
   - Save generated chapters, plot outlines, and validation results.  
   - Enable multiple project management with separate save files.

---

## ✍️ Phase 3 — Creative Control

6. **Manual Chapter Editing**  
   - Let users manually edit chapters within the interface.

7. **AI Chat per Chapter**  
   - Add an interactive chat system where users can discuss or request edits for a specific chapter.  
   - A supervising LLM will analyze whether requested changes affect **subsequent chapters** and, if necessary, **update them iteratively**.

---

## 🎨 Phase 4 — Presentation and Distribution

8. **Generate EPUB Cover Image**  
   - Automatically create an AI-generated book cover (based on story theme or user input).  
   - Potential integration with **ComfyUI** for image workflows.

9. **Make the Repository Public**  
   - Publish the GitHub repository and prepare documentation for open collaboration.

---

## 🧠 Phase 5 — Advanced AI Features

10. **Book Comparison System**  
    - Enable users to compare multiple books using pre-defined or custom criteria.  
    - Comparison will be performed **pairwise in a tournament-style bracket**:  
      - 4 books → 2 semifinals → 1 final round → overall winner suggested by the LLM.

11. **Graphic Story Generation**  
    - Generate illustrated or visualized stories by adding AI-generated images throughout the chapters.

12. **Model Selection per Task**  
    - Allow choosing different LLMs for specific tasks (e.g., chapter generation, validation, editing).  
    - Integrate with **OpenAI** and potentially other model providers.

---

## 🚧 Status

| Feature | Status |
|----------|--------|
| Update README | ⏳ Planned |
| Genre Selection in UI | ⏳ Planned |
| Export to EPUB | ⏳ Planned |
| Prompt Optimization | ⏳ Planned |
| Saving Project State | ⏳ Planned |
| Manual Chapter Editing | ⏳ Planned |
| AI Chat per Chapter | 🔜 Future |
| EPUB Cover Generation | 🔜 Future |
| Public GitHub Repository | 🔜 Future |
| Book Comparison System | 🔜 Future |
| Graphic Story Generation | 🔜 Future |
| Model Selection per Task | 🔜 Future |

---

**Last updated:** October 2025  
**Maintained by:** Gabriel C.
