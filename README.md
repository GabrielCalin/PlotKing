# BookKing - Live AI Story Planner

BookKing is an interactive AI-powered application that helps writers generate, validate, and refine novel outlines. The application takes a short plot description and transforms it into a complete chapter-by-chapter outline through a three-step pipeline process.

## Features

- **Plot Expansion**: Transform a brief plot idea into a detailed, structured plot summary
- **Chapter Generation**: Automatically create chapter titles and descriptions based on the expanded plot
- **Validation & Refinement**: Analyze and improve chapter coherence with AI feedback
- **Interactive UI**: Monitor the generation process in real-time through a Gradio interface

## Architecture

The application follows a three-step pipeline architecture:

### Step 1: Plot Expander (`step1_plot_expander.py`)
- Takes a user's short plot description as input
- Uses an AI model to expand it into a structured, objective plot summary (700-1000 words)
- Maintains the user's main concept, characters, and relationships
- Structures the plot in three parts: setup, conflict, and resolution

### Step 2: Chapter Generator (`step2_chapter_generator.py`)
- Takes the expanded plot from Step 1 as input
- Generates a specified number of chapter titles and descriptions
- Each chapter description summarizes key events or turning points
- Maintains a neutral and factual tone

### Step 3: Validator (`step3_validator.py`)
- Takes both the expanded plot and generated chapters as input
- Validates if the chapters are coherent and consistent with the plot
- Provides feedback for improvements if necessary
- Supports an iterative refinement process (up to 3 validation attempts)

## Workflow

1. User enters a short plot description and desired number of chapters
2. The system expands the plot using the Plot Expander
3. The expanded plot is fed to the Chapter Generator to create chapter outlines
4. The Validator checks the coherence between the plot and chapters
5. If validation fails, the system regenerates chapters with feedback
6. This process repeats until validation passes or max attempts are reached
7. The final output is a complete, validated novel outline

## Requirements

The application requires:
- Python 3.6+
- Gradio for the UI
- Access to a local LLM API (default: http://localhost:1234/v1/chat/completions)
- Additional dependencies listed in `requirements.txt`

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Run the application: `python main_app.py` or `./run.sh`
3. Access the UI through your browser at `http://localhost:7860`

## Technical Details

- The application uses a local LLM API for all AI operations
- Default model is "mistral" for plot expansion and chapter generation
- Validation uses "phi-3-mini-4k-instruct" model
- The system implements a feedback loop for chapter refinement
- Real-time progress updates are streamed to the UI