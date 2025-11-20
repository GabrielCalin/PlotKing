# 🗺️ AI Story Generator — Roadmap

This document outlines the planned development milestones for the **AI Story Generator** project, prioritized by implementation phase.

---

## 🧭 Phase 2 — User Experience & Creativity Tools

9. **AI Chat per Chapter**  
   - Add an interactive chat panel to discuss or request changes for a specific chapter.  
   - A supervising LLM ensures narrative consistency and, when necessary, re-writes dependent chapters.

10. **Add Empty Chapters (Writer Assist Mode)**  
   - Let users insert blank chapters manually.  
   - Intended to help writers start or continue their own text with AI assistance.

11. **Stop Edit Pipeline**  
   - Allow users to stop/cancel the edit pipeline while it's running.  
   - Gracefully handle partial completion and preserve any completed edits.

12. **Draft Review System**  
   - When the edit pipeline finishes, all changes are saved as drafts.  
   - User is presented with choices: **revert all**, **accept all**, **regenerate partial**, and **accept partial**.  
   - View changes with change coloring (added/deleted/modified text highlighting).

---

## 🎨 Phase 3 — Presentation and Export

13. **Export to EPUB**  
   - Export full books as `.epub` files with metadata. 

14. **Public GitHub Repository**  
   - Make the project public and document setup, dependencies, and contribution flow.

15. **Generate EPUB Cover Image**  
   - Automatically create covers based on title, genre, and plot.  
   - Optional integration with **ComfyUI** or external image workflows.

---

## ✍️ Phase 4 — Story Growth and Structure Control

16. **AI Chat for Refined Plot**  
   - Generate a refined plot based on an interactive chat conversation.  
   - Users can discuss plot improvements, character arcs, and story structure through natural conversation.  
   - The AI generates an updated plot that incorporates the discussion points.

17. **Infill Chapters**  
   - Add the ability to insert a new chapter **between existing ones** to fill narrative gaps.  
   - Automatically update chapter numbering and summary references.

18. **Outfill Chapters**  
   - Continue an existing book with **new chapters** beyond the planned structure.  
   - Preserve continuity by referencing the final chapters.

---

## ⚙️ Phase 5 — Configuration & Customization

19. **Settings Tab**  
   - Add a settings section for advanced parameters:  
     - Model selection per task.  
     - Max tokens per chapter.  
     - Timeout and retry policies.  
     - Context window behavior (summaries vs full chapter inclusion).  
     - Temperature, top-p, and verbosity controls.

20. **Model Selection per Task**  
   - Choose separate models for each step (e.g., validation vs writing).  
   - Integration with **OpenAI**, **LM Studio**, or **local LLMs**.

21. **Automatic Translation**  
   - Add automatic **multi-language translation** for full books or chapters.  
   - Universal model-agnostic design, with export to any supported language.  

---

## 💬 Phase 6 — Advanced Interaction & Collaboration

22. **Advanced Cross-Chapter Chat**  
   - A global AI chat that can handle **multi-chapter edits** and **story-level refactoring**.  
   - Allows broader transformations such as tone adjustment, pacing changes, or multi-arc restructuring.

23. **Character & Object Modification**  
   - Provide an interface to modify a character's **personality, appearance, relationships, or role**.  
   - Extendable to modify **key objects** or **locations** across chapters.  
   - System ensures consistency by updating references in future (and optionally past) chapters.

24. **Import Ebooks**  
   - Add the ability to import existing ebooks (EPUB, MOBI, etc.) into the system.  
   - Parse imported books into chapters and structure.  
   - Users can then expand or modify the imported book using all available editing tools.

---

## 🧠 Phase 7 — Experimental & Research Features

25. **Book Comparison System**  
   - Compare multiple books via pairwise evaluation (e.g., 4-book tournament → semifinals → final).  
   - Criteria: writing quality, consistency, emotional impact, etc.

26. **Generate Audio Book**  
   - Convert generated chapters to **narrated audio** using text-to-speech (TTS).  
   - Voices adjustable by tone, gender, and style (narrative, dramatic, cinematic).  
   - Export as MP3/FLAC or integrated audio player in UI.

27. **Graphic Story Generation**  
   - Enrich stories with AI-generated illustrations per chapter.

28. **Embedded LLMs & Research-Driven Non-Fiction Mode**  
   - Add support for embedded or local assistant models to perform factual research before writing.  
   - Ideal for **biographies, essays, or technical non-fiction** where factual correctness is essential.  
   - *Low priority / experimental feature.*

---

## 🚧 Status

| Feature | Status |
|----------|--------|
| **AI Chat per Chapter** | ⏳ In Progress |
| **Add Empty Chapters (Writer Assist Mode)** | ⏳ Planned |
| **Stop Edit Pipeline** | ⏳ Planned |
| **Draft Review System** | ⏳ Planned |
| **Export to EPUB** | 🔜 Future |
| **Public GitHub Repository** | 🔜 Future |
| **Generate EPUB Cover Image** | 🔜 Future |
| **AI Chat for Refined Plot** | 🔜 Future |
| **Infill Chapters** | 🔜 Future |
| **Outfill Chapters** | 🔜 Future |
| **Settings Tab** | 🔜 Future |
| **Model Selection per Task** | 🔜 Future |
| **Automatic Translation** | 🔜 Future |
| **Advanced Cross-Chapter Chat** | 🔜 Future |
| **Character & Object Modification** | 🔜 Future |
| **Import Ebooks** | 🔜 Future |
| **Book Comparison System** | 🔬 Experimental |
| **Generate Audio Book** | 🔬 Experimental |
| **Graphic Story Generation** | 🔬 Experimental |
| **Embedded LLMs / Research Non-Fiction Mode** | 🔬 Experimental |

---

**Last updated:** November 2025  
**Maintained by:** Gabriel C.
