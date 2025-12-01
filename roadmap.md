# 🗺️ AI Story Generator — Roadmap

This document outlines the planned development milestones for the **AI Story Generator** project, prioritized by implementation phase.

---

## 🎨 Phase 3 — Presentation and Export

12. **Export to EPUB**  
   - Export full books as `.epub` files with metadata. 

13. **Public GitHub Repository**  
   - Make the project public and document setup, dependencies, and contribution flow.

14. **Generate EPUB Cover Image**  
   - Automatically create covers based on title, genre, and plot.  
   - Optional integration with **ComfyUI** or external image workflows.

---

## ✍️ Phase 4 — Story Growth and Structure Control

15. **AI Chat for Refined Plot**  
   - Generate a refined plot based on an interactive chat conversation.  
   - Users can discuss plot improvements, character arcs, and story structure through natural conversation.  
   - The AI generates an updated plot that incorporates the discussion points.

16. **Add Empty Chapters (Writer Assist Mode)**  
   - Let users insert blank chapters manually.  
   - Intended to help writers start or continue their own text with AI assistance.

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
   - **Main Language System**: There will be a main language, and translated versions will only allow either re-generation from scratch or generation with minimal changes + manual edits.  

---

## 💬 Phase 6 — Advanced Interaction & Collaboration

22. **Advanced Cross-Chapter Chat**  
   - A global AI chat that can handle **multi-chapter edits** and **story-level refactoring**.  
   - Allows broader transformations such as tone adjustment, pacing changes, or multi-arc restructuring.

23. **Character & Object Modification**  
   - Provide an interface to modify a character's **personality, appearance, relationships, or role**.  
   - Extendable to modify **key objects** or **locations** across chapters.  
   - System ensures consistency by updating references in future (and optionally past) chapters.

24. **Visual Plot Design**  
   - A new tab to visualize main events, characters, etc. (e.g., circles for plot items).  
   - Allows easy definition of parallel narrative threads and their intersections.  
   - Helps in understanding and defining the story structure visually.

25. **Import Ebooks**  
   - Add the ability to import existing ebooks (EPUB, MOBI, etc.) into the system.  
   - Parse imported books into chapters and structure.  
   - Users can then expand or modify the imported book using all available editing tools.

26. **Book Continuations**  
   - Support for book sequels (Part 2).  
   - Support for copying the narrative style of another book (Persona definitions).

27. **Global Draft System**  
   - Switch between edit modes and add to a 'draft', validating only at the end.  
   - Edit and chat with the validator based on results.  
   - Support for undo/redo + quick save project.

---

## 🧠 Phase 7 — Experimental & Research Features

28. **Book Comparison System**  
   - Compare multiple books via pairwise evaluation (e.g., 4-book tournament → semifinals → final).  
   - Criteria: writing quality, consistency, emotional impact, etc.  
   - **Version History**: Support for multiple book generations stored and selectable as part of the same project.  
   - Project save structure will save all versions (preferably in different files for speed). Comparison runs between these versions.

29. **Generate Audio Book**  
   - Convert generated chapters to **narrated audio** using text-to-speech (TTS).  
   - Voices adjustable by tone, gender, and style (narrative, dramatic, cinematic).  
   - Export as MP3/FLAC or integrated audio player in UI.

30. **Graphic Story Generation**  
   - Enrich stories with AI-generated illustrations per chapter.

31. **Embedded LLMs & Research-Driven Non-Fiction Mode**  
   - Add support for embedded or local assistant models to perform factual research before writing.  
   - Ideal for **biographies, essays, or technical non-fiction** where factual correctness is essential.  
   - *Low priority / experimental feature.*

---

## 🚧 Status

| Feature | Status |
|----------|--------|
| **Export to EPUB** | ⏳ In Progress |
| **Public GitHub Repository** | 🔜 Future |
| **Generate EPUB Cover Image** | 🔜 Future |
| **AI Chat for Refined Plot** | 🔜 Future |
| **Add Empty Chapters (Writer Assist Mode)** | ⏳ Planned |
| **Infill Chapters** | 🔜 Future |
| **Outfill Chapters** | 🔜 Future |
| **Settings Tab** | 🔜 Future |
| **Model Selection per Task** | 🔜 Future |
| **Automatic Translation** | 🔜 Future |
| **Advanced Cross-Chapter Chat** | 🔜 Future |
| **Character & Object Modification** | 🔜 Future |
| **Visual Plot Design** | 🔜 Future |
| **Import Ebooks** | 🔜 Future |
| **Book Continuations** | 🔜 Future |
| **Global Draft System** | 🔜 Future |
| **Book Comparison System** | 🔬 Experimental |
| **Generate Audio Book** | 🔬 Experimental |
| **Graphic Story Generation** | 🔬 Experimental |
| **Embedded LLMs / Research Non-Fiction Mode** | 🔬 Experimental |

---

**Last updated:** November 2025  
**Maintained by:** Gabriel C.
