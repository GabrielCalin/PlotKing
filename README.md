# BookKing - AI Story Builder

BookKing is an interactive AI-powered application that helps writers generate, validate, and refine novel outlines. The application takes a short plot description and transforms it into a complete book using local LLM deployments.

![alt text](image.png)

## Features

- **Plot Expansion**: Transform a brief plot idea into a detailed, structured plot summary
- **Chapter Generation**: Automatically create chapter titles and descriptions based on the expanded plot, then generate the **full chapter text** for each section of the story.
- **Chapter Verification System**: After each chapter is generated, an AI model validates it against the original plot and previous chapters. If validation fails, the system automatically regenerates the chapter until it passes.
- **Interactive UI**: Monitor the generation process in real-time through a Gradio interface

## Workflow

1. User enters a short plot description and desired number of chapters
2. The system expands the plot.
3. The expanded plot serves as the basis for generating detailed chapter outlines, defining the structure and flow of the story.
4. A validator checks the coherence between the plot and chapters.
5. If validation fails, the system regenerates chapters outlines based on validator feedback.
6. This process repeats until validation passes.
7. Each chapter is then generated.
8. Each chapter is validated to ensure it meets the desired quality and continuity criteria, and that it aligns with its original outline description.
9. The final output is a complete, validated novel with full chapters

## Requirements

The application requires:
- Python 3.6+
- Gradio for the UI
- Access to a local LLM API (default: http://localhost:1234/v1/chat/completions)
- Additional dependencies listed in `requirements.txt`

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Run the application: `python main_app.py` or `./run.bat` on Windows.
3. Access the UI through your browser at `http://localhost:7860`
