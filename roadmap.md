# 🗺️ AI Story Generator — Roadmap

This document outlines the planned development milestones for the **AI Story Generator** project, prioritized by implementation phase.

---

## 🎨 Phase 3 — Presentation and Export

15. **Generate EPUB Cover Image**  
   - Automatically create covers based on title, genre, and plot.  
   - Optional integration with **ComfyUI** or external image workflows.

---

## ✍️ Phase 4 — Story Growth and Structure Control

16. **AI Chat for Refined Plot**  
   - Generate a refined plot based on an interactive chat conversation.  
   - Users can discuss plot improvements, character arcs, and story structure through natural conversation.  
   - The AI generates an updated plot that incorporates the discussion points.

17. **Global Draft System**  
   - Switch between edit modes and add to a 'draft', validating only at the end.  
   - Support for undo/redo + quick save project.

18. **Add Empty Chapters (Writer Assist Mode)**  
   - Let users insert blank chapters manually.  
   - Intended to help writers start or continue their own text with AI assistance.

19. **Infill Chapters**  
   - Add the ability to insert a new chapter **between existing ones** to fill narrative gaps.  
   - Automatically update chapter numbering and summary references.

20. **Outfill Chapters**  
   - Continue an existing book with **new chapters** beyond the planned structure.  
   - Preserve continuity by referencing the final chapters.

---

## ⚙️ Phase 5 — Configuration & Customization

21. **Settings Tab**  
   - Add a settings section for advanced parameters:  
     - Model selection per task.  
     - Max tokens per chapter.  
     - Timeout and retry policies.  
     - Context window behavior (summaries vs full chapter inclusion).  
     - Temperature, top-p, and verbosity controls.

22. **Model Selection per Task**  
   - Choose separate models for each step (e.g., validation vs writing).  
   - Integration with **OpenAI**, **LM Studio**, or **local LLMs**.

23. **Automatic Translation**  
   - Add automatic **multi-language translation** for full books or chapters.  
   - Universal model-agnostic design, with export to any supported language.  
   - **Main Language System**: There will be a main language, and translated versions will only allow either re-generation from scratch or generation with minimal changes + manual edits.  

---

## 💬 Phase 6 — Advanced Interaction & Collaboration

25. **Advanced Cross-Chapter Chat**  
   - A global AI chat that can handle **multi-chapter edits** and **story-level refactoring**.  
   - Allows broader transformations such as tone adjustment, pacing changes, or multi-arc restructuring.  
   - Edit and chat with the validator based on results.

26. **Character & Object Modification**  
   - Provide an interface to modify a character's **personality, appearance, relationships, or role**.  
   - Extendable to modify **key objects** or **locations** across chapters.  
   - System ensures consistency by updating references in future (and optionally past) chapters.

27. **Automated Tests (UI Scenario Based)**  
   - Implement automated UI tests based on user scenarios.  
   - Test critical workflows end-to-end to ensure reliability and prevent regressions.

28. **Switch from Gradio Frontend**  
   - Migrate from Gradio to a more flexible frontend framework.  
   - Improve UI/UX capabilities and performance.

29. **Visual Plot Design**  
   - A new tab to visualize main events, characters, etc. (e.g., circles for plot items).  
   - Allows easy definition of parallel narrative threads and their intersections.  
   - Helps in understanding and defining the story structure visually.

30. **Import Ebooks**  
   - Add the ability to import existing ebooks (EPUB, MOBI, etc.) into the system.  
   - Parse imported books into chapters and structure.  
   - Users can then expand or modify the imported book using all available editing tools.

31. **Book Continuations**  
   - Support for book sequels (Part 2).  
   - Support for copying the narrative style of another book (Persona definitions).

---

## 🧠 Phase 7 — Experimental & Research Features

33. **Book Comparison System**  
   - Compare multiple books via pairwise evaluation (e.g., 4-book tournament → semifinals → final).  
   - Criteria: writing quality, consistency, emotional impact, etc.  
   - **Version History**: Support for multiple book generations stored and selectable as part of the same project.  
   - Project save structure will save all versions (preferably in different files for speed). Comparison runs between these versions.

34. **Advanced Custom Templating for EPUB Format**  
   - Implement advanced custom templating for EPUB format.  
   - Either build from scratch or use an existing templating library.  
   - Allow users to customize EPUB output with custom styles, layouts, and formatting.

35. **Generate Audio Book**  
   - Convert generated chapters to **narrated audio** using text-to-speech (TTS).  
   - Voices adjustable by tone, gender, and style (narrative, dramatic, cinematic).  
   - Export as MP3/FLAC or integrated audio player in UI.

36. **Graphic Story Generation**  
   - Enrich stories with AI-generated illustrations per chapter.

37. **Embedded LLMs & Research-Driven Non-Fiction Mode**  
   - Add support for embedded or local assistant models to perform factual research before writing.  
   - Ideal for **biographies, essays, or technical non-fiction** where factual correctness is essential.  
   - *Low priority / experimental feature.*

38. **REST API**  
   - Provide a REST API for programmatic access to the story generation system.  
   - Enable integration with external tools and automation workflows.  
   - *Low priority / experimental feature.*

39. **Custom Blocks (ComfyUI-style)**  
   - Implement a visual node-based interface similar to ComfyUI for workflow customization.  
   - Allow users to create custom processing blocks and connect them visually.  
   - *Low priority / experimental feature.*

---

## 🚧 Status

| Feature | Status |
|----------|--------|
| **Generate EPUB Cover Image** | ⏳ In Progress |
| **AI Chat for Refined Plot** | ⏳ Planned |
| **Global Draft System** | ⏳ Planned |
| **Add Empty Chapters (Writer Assist Mode)** | ⏳ Planned |
| **Infill Chapters** | ⏳ Planned |
| **Outfill Chapters** | ⏳ Planned |
| **Settings Tab** | ⏳ Planned |
| **Model Selection per Task** | ⏳ Planned |
| **Automatic Translation** | ⏳ Planned |
| **Advanced Cross-Chapter Chat** | ⏳ Planned |
| **Character & Object Modification** | ⏳ Planned |
| **Automated Tests (UI Scenario Based)** | ⏳ Planned |
| **Switch from Gradio Frontend** | ⏳ Planned |
| **Visual Plot Design** | ⏳ Planned |
| **Import Ebooks** | ⏳ Planned |
| **Book Continuations** | ⏳ Planned |
| **Book Comparison System** | 🔬 Experimental |
| **Advanced Custom Templating for EPUB Format** | 🔬 Experimental |
| **Generate Audio Book** | 🔬 Experimental |
| **Graphic Story Generation** | 🔬 Experimental |
| **Embedded LLMs / Research Non-Fiction Mode** | 🔬 Experimental |
| **REST API** | 🔬 Experimental |
| **Custom Blocks (ComfyUI-style)** | 🔬 Experimental |

---

**Last updated:** December 2025  
**Maintained by:** Gabriel C.
