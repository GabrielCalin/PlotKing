# 🗺️ AI Story Generator — Roadmap

This document outlines the planned development milestones for the **AI Story Generator** project, prioritized by implementation phase.

---

## ✅ Phase 1 — Core Validation & Quality of Life

1. **QOL updates**  
   - Add timestamp prefix to Process Log.  
   - Increase max token limit for the chapter writer.  
   - Update main documentation and README.

2. **Book Genre Selection in UI**  
   - Add a genre text bo input in the interface.  
   - The selected genre will influence the tone, writing style, and narrative focus of generated plots and chapters.

3. **Generate Plot Idea**  
   - Generate **similar plot ideas** based on user input.  
   - Serves as the starting point for the book generation pipeline.

---

## 🧭 Phase 2 — User Experience & Creativity Tools

4. **Prompt Optimization**  
   - Refine prompts for each stage (plot expansion, chapter generation, validation) to improve quality and narrative coherence.

5. **Saving Project State**  
   - Enable saving and resuming work sessions.  
   - Save expanded plot, chapters, validation logs, and progress metadata.  
   - Support multiple concurrent projects.

6. **Manual Chapter Editing**  
   - Allow users to edit any generated chapter directly within the interface.
   - Trigger regenerations if plot changes. 

7. **AI Editing on Selected Text**  
    - Enable users to **select a portion of text** and apply quick AI edits (rewrite, expand, simplify, etc.).

8. **AI Chat per Chapter**  
    - Add an interactive chat panel to discuss or request changes for a specific chapter.  
    - A supervising LLM ensures narrative consistency and, when necessary, re-writes dependent chapters.

9. **Add Empty Chapters (Writer Assist Mode)**  
   - Let users insert blank chapters manually.  
   - Intended to help writers start or continue their own text with AI assistance.

---

## 🎨 Phase 3 — Presentation and Export

10. **Export to EPUB**  
    - Export full books as `.epub` files with metadata and optional AI-generated cover.  

11. **Generate EPUB Cover Image**  
    - Automatically create covers based on title, genre, and plot.  
    - Optional integration with **ComfyUI** or external image workflows.

12. **Public GitHub Repository**  
    - Make the project public and document setup, dependencies, and contribution flow.

---

## ✍️ Phase 4 — Story Growth and Structure Control

13. **Infill Chapters**  
   - Add the ability to insert a new chapter **between existing ones** to fill narrative gaps.  
   - Automatically update chapter numbering and summary references.

14. **Outfill Chapters**  
   - Continue an existing book with **new chapters** beyond the planned structure.  
   - Preserve continuity by referencing the final chapters.

---

## 💬 Phase 5 — Advanced Interaction & Collaboration

15. **Advanced Cross-Chapter Chat**  
    - A global AI chat that can handle **multi-chapter edits** and **story-level refactoring**.  
    - Allows broader transformations such as tone adjustment, pacing changes, or multi-arc restructuring.

16. **Character & Object Modification**  
    - Provide an interface to modify a character’s **personality, appearance, relationships, or role**.  
    - Extendable to modify **key objects** or **locations** across chapters.  
    - System ensures consistency by updating references in future (and optionally past) chapters.

---

## ⚙️ Phase 6 — Configuration & Customization

17. **Settings Tab**  
    - Add a settings section for advanced parameters:  
      - Model selection per task.  
      - Max tokens per chapter.  
      - Timeout and retry policies.  
      - Context window behavior (summaries vs full chapter inclusion).  
      - Temperature, top-p, and verbosity controls.

18. **Model Selection per Task**  
    - Choose separate models for each step (e.g., validation vs writing).  
    - Integration with **OpenAI**, **LM Studio**, or **local LLMs**.

---

## 🧠 Phase 7 — Experimental & Research Features

19. **Book Comparison System**  
    - Compare multiple books via pairwise evaluation (e.g., 4-book tournament → semifinals → final).  
    - Criteria: writing quality, consistency, emotional impact, etc.

20. **Graphic Story Generation**  
    - Enrich stories with AI-generated illustrations per chapter.

21. **Embedded LLMs & Research-Driven Non-Fiction Mode**  
    - Add support for embedded or local assistant models to perform factual research before writing.  
    - Ideal for **biographies, essays, or technical non-fiction** where factual correctness is essential.  
    - *Low priority / experimental feature.*

---

## 🚧 Status

| Feature | Status |
|----------|--------|
| **QOL updates** | ⏳ In Progress |
| **Book Genre Selection in UI** | ⏳ Planned |
| **Generate Plot Idea** | ⏳ Planned |
| **Prompt Optimization** | ⏳ Planned |
| **Saving Project State** | ⏳ Planned |
| **Manual Chapter Editing** | ⏳ Planned |
| **AI Editing on Selected Text** | ⏳ Planned |
| **AI Chat per Chapter** | ⏳ Planned |
| **Add Empty Chapters (Writer Assist Mode)** | ⏳ Planned |
| **Export to EPUB** | 🔜 Future |
| **Generate EPUB Cover Image** | 🔜 Future |
| **Public GitHub Repository** | 🔜 Future |
| **Infill Chapters** | 🔜 Future |
| **Outfill Chapters** | 🔜 Future |
| **Advanced Cross-Chapter Chat** | 🔜 Future |
| **Character & Object Modification** | 🔜 Future |
| **Settings Tab** | 🔜 Future |
| **Model Selection per Task** | 🔜 Future |
| **Book Comparison System** | 🔬 Experimental |
| **Graphic Story Generation** | 🔬 Experimental |
| **Embedded LLMs / Research Non-Fiction Mode** | 🔬 Experimental |

---

**Last updated:** October 2025  
**Maintained by:** Gabriel C.
