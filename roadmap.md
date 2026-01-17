# 🗺️ AI Story Generator — Roadmap

This document outlines the planned development milestones for the **AI Story Generator** project, prioritized by implementation phase.

---

## ⚙️ Phase 5 — Configuration & Customization

23. **Advanced Settings**  
   - Add a settings section for advanced parameters:  
     - Max tokens per chapter.  
     - Timeout and retry policies.  
     - Temperature, top-p, and verbosity controls.  
     - Reasoning parameters (reasoning effort, etc.).  
     - Prompt Customization.  

24. **Pipeline Improvements**  
   - At validate after edit, provide sequentially: expanded plot, chapter overview, and chapters.  
   - Extract chapter descriptions as a list with AI before generating a chapter, providing only the description of the chapter to be generated + full previous chapters, not descriptions of all chapters.  
   - Option for Summarize instead of Full Chapters in the context provided to the LLM when writing a new chapter, with Summarize also defining things like open points, things to remember for the next sections.  
   - Method for chapters overview for many chapters to generate correctly (currently either if there are many it doesn't write them all, or they become shorter towards the end).  
   - Call replace tools at editor - chat instead of full regeneration with an intent analyzer that decides if there are small changes (so call replace tools) or large (regeneration).  
   - Run validator on demand per section as part of view mode, visible when viewing a checkpoint.  
   - Parse chapter summary to list and insert summary programmatically at fill.  
   - Pipeline for modifications from fill chat - implement a structured pipeline that includes: planning phase (similar to ChatGPT reasoning) where the system considers which characters don't yet have permission to appear, what events will be included, how to start to fit perfectly with the previous chapter, and where to end to fit perfectly with the beginning of the next chapter; tool call for chapter generation; validation step; then respond to the user.

25. **Dockerfile and Docker Hub PlotKing**  
   - Create Dockerfile for PlotKing.  
   - Publish PlotKing image to Docker Hub.

26. **Automatic Translation**  
   - Add automatic **multi-language translation** for full books or chapters.  
   - Universal model-agnostic design, with export to any supported language.  
   - **Main Language System**: There will be a main language, and translated versions will only allow either re-generation from scratch or generation with minimal changes + manual edits.  

27. **Editor Functions in Manual Mode**  
   - Add formatting options (bold, italic, etc.) for manual editing mode.

---

## 💬 Phase 6 — Advanced Interaction & Collaboration

28. **Advanced Cross-Chapter Chat**  
   - A global AI chat that can handle **multi-chapter edits** and **story-level refactoring**.  
   - Allows broader transformations such as tone adjustment, pacing changes, or multi-arc restructuring.  
   - Edit and chat with the validator based on results.

29. **Save Improvements**  
   - Automatically save project when writing to checkpoint.  
   - Also automatically save drafts to prevent their loss.  

30. **Regen Edit Mode**  
   - Non-destructive chapter regeneration that doesn't trigger regeneration of all subsequent chapters.  
   - New edit mode specifically for regeneration workflows.  
   - Support for regeneration levels: from scratch, preserve minimum, preserve medium, preserve majority, etc.  

31. **Support for Remove Chapter**  
   - Destructive operation for removing chapters.  
   - Can have force edit or special validation that warns what is lost by deleting and what gaps appear.  
   - Only allows force edit after validation.  
   - Includes merge from chapters overview edit.

32. **Regenerate Response in Chat Edit Mode**  
   - Add ability to regenerate AI responses within the chat edit interface.

33. **Regenerate Multiple Times in Regenerate Generated Draft**  
   - Support for regenerating drafts multiple times (e.g., 5 times) to get variations.

34. **Character & Object Modification**  
   - Provide an interface to modify a character's **personality, appearance, relationships, or role**.  
   - Extendable to modify **key objects** or **locations** across chapters.  
   - System ensures consistency by updating references in future (and optionally past) chapters.

35. **Automated Tests (UI Scenario Based)**  
   - Implement automated UI tests based on user scenarios.  
   - Test critical workflows end-to-end to ensure reliability and prevent regressions.  
   - Automated tests chosen by AI from the entire suite based on diff branch vs master.  
   - Tests defined in human language.  
   - Run in browser by AI.

36. **Switch from Gradio Frontend**  
   - Migrate from Gradio to a more flexible frontend framework.  
   - Improve UI/UX capabilities and performance.

37. **Visual Plot Design**  
   - A new tab to visualize main events, characters, etc. (e.g., circles for plot items).  
   - Allows easy definition of parallel narrative threads and their intersections.  
   - Helps in understanding and defining the story structure visually.

38. **Complex Chapter Numbering**  
   - Support for sub-chapters, book parts, and hierarchical chapter structures.  
   - Flexible numbering system (e.g., Part 1, Chapter 2.1, Chapter 2.2, etc.).  
   - Maintains proper references and navigation throughout the book structure.

39. **Import Ebooks**  
   - Add the ability to import existing ebooks (EPUB, MOBI, etc.) into the system.  
   - Parse imported books into chapters and structure.  
   - Users can then expand or modify the imported book using all available editing tools.

40. **Book Continuations**  
   - Support for book sequels (Part 2).  
   - Support for copying the narrative style of another book (Persona definitions).

---

## 🧠 Phase 7 — Experimental & Research Features

41. **Critic Mode**  
   - Review book style with comprehensive feedback including strengths, weaknesses, and overall assessment.  
   - Provide detailed critique covering writing quality, narrative consistency, character development, pacing, etc.  
   - Optional rating system for overall book quality.  
   - Helps identify areas for improvement and highlights what works well.

42. **Book Comparison System**  
   - Compare multiple books via pairwise evaluation (e.g., 4-book tournament → semifinals → final).  
   - Criteria: writing quality, consistency, emotional impact, etc.  
   - **Version History**: Support for multiple book generations stored and selectable as part of the same project.  
   - Project save structure will save all versions (preferably in different files for speed). Comparison runs between these versions.

43. **Advanced Custom Templating for EPUB Format**  
   - Implement advanced custom templating for EPUB format.  
   - Either build from scratch or use an existing templating library.  
   - Allow users to customize EPUB output with custom styles, layouts, and formatting.

44. **Generate Audio Book**  
   - Convert generated chapters to **narrated audio** using text-to-speech (TTS).  
   - Voices adjustable by tone, gender, and style (narrative, dramatic, cinematic).  
   - Export as MP3/FLAC or integrated audio player in UI.

45. **Automatic Podcast (Radio)**  
   - Generate automated podcast episodes based on selected topics or book content.  
   - Real-time command interface to modify what's being presented during podcast generation.  
   - Dynamic content adjustment and interactive control over podcast flow and presentation style.

46. **Graphic Story Generation**  
   - Enrich stories with AI-generated illustrations per chapter.

47. **Embedded LLMs & Research-Driven Non-Fiction Mode**  
   - Add support for embedded or local assistant models to perform factual research before writing.  
   - Ideal for **biographies, essays, or technical non-fiction** where factual correctness is essential.  
   - *Low priority / experimental feature.*

48. **Interactive / Gamified Story Creation**  
   - Add interactive and gamified elements to the story creation process.

49. **Multiple Users and Sessions**  
   - Support for multiple users working on the same or different projects simultaneously.  
   - Session management for collaborative editing and individual workspaces.  
   - User authentication and permission management for shared projects.

50. **REST API**  
   - Provide a REST API for programmatic access to the story generation system.  
   - Enable integration with external tools and automation workflows.  
   - *Low priority / experimental feature.*

51. **Custom Blocks (ComfyUI-style)**  
   - Implement a visual node-based interface similar to ComfyUI for workflow customization.  
   - Allow users to create custom processing blocks and connect them visually.  
   - *Low priority / experimental feature.*

52. **Book Reader**  
   - Integrated book reader interface for reading generated or imported stories.  
   - Chat support for discussing the book content, asking questions, or getting clarifications.  
   - Built-in translation functionality for tranlating words or sentences,

---

## 🚧 Status

| Feature | Status |
|----------|--------|
| **Advanced Settings** | ⏳ In Progress |
| **Pipeline Improvements** | ⏳ Planned |
| **Dockerfile and Docker Hub PlotKing** | ⏳ Planned |
| **Automatic Translation** | ⏳ Planned |
| **Editor Functions in Manual Mode** | ⏳ Planned |
| **Advanced Cross-Chapter Chat** | ⏳ Planned |
| **Save Improvements** | ⏳ Planned |
| **Regen Edit Mode** | ⏳ Planned |
| **Support for Remove Chapter** | ⏳ Planned |
| **Regenerate Response in Chat Edit Mode** | ⏳ Planned |
| **Regenerate Multiple Times (x5) in Regenerate Generated Draft** | ⏳ Planned |
| **Character & Object Modification** | ⏳ Planned |
| **Automated Tests (UI Scenario Based)** | ⏳ Planned |
| **Switch from Gradio Frontend** | ⏳ Planned |
| **Visual Plot Design** | ⏳ Planned |
| **Complex Chapter Numbering** | ⏳ Planned |
| **Import Ebooks** | ⏳ Planned |
| **Book Continuations** | ⏳ Planned |
| **Critic Mode** | 🔬 Experimental |
| **Book Comparison System** | 🔬 Experimental |
| **Advanced Custom Templating for EPUB Format** | 🔬 Experimental |
| **Generate Audio Book** | 🔬 Experimental |
| **Automatic Podcast (Radio)** | 🔬 Experimental |
| **Graphic Story Generation** | 🔬 Experimental |
| **Embedded LLMs / Research Non-Fiction Mode** | 🔬 Experimental |
| **Interactive / Gamified Story Creation** | 🔬 Experimental |
| **Multiple Users and Sessions** | 🔬 Experimental |
| **REST API** | 🔬 Experimental |
| **Custom Blocks (ComfyUI-style)** | 🔬 Experimental |
| **Book Reader** | 🔬 Experimental |

---

**Last updated:** December 2025  
**Maintained by:** Gabriel C.
