# Local AI Culling

Local AI Culling is a completely offline, privacy-first, AI-assisted image culling tool built specifically for professional photographers. It analyzes your raw photo shoots, groups bursts, detects duplicates, evaluates technical quality (focus, noise, composition, expressions), and automatically organizes your images into `KEEP`, `REVIEW`, and `REJECT` folders so you can immediately begin editing your best work in Adobe Lightroom or your preferred editor.

Because it runs 100% locally on your own hardware, your photographs are never uploaded to the cloud, ensuring total client privacy and eliminating subscription fees.

## Features

- **Duplicate Detection**: Groups visually identical photos taken moments apart.
- **Burst Detection & Ranking**: Identifies high-speed bursts and automatically selects the single best frame.
- **Intelligent Classification**: Sorts images into `KEEP`, `REVIEW`, and `REJECT` based on customizable scoring.
- **Expression Intelligence**: Understands facial semantics (e.g., closed eyes, blinking, awkward mouth shapes) to avoid penalizing artistic choices while flagging ruined shots.
- **Image Editability Engine**: Simulates shadow and highlight recovery on the raw preview to estimate real-world editability (penalizing noise and color degradation).
- **Scene Intelligence**: Detects environmental and subject context (e.g., weddings, portraits, low-light).
- **Photographer Feedback Dashboard**: A local web interface to review decisions, adjust thresholds, and understand exactly *why* the AI made a decision.
- **Hardlink Export Engine**: Instantly creates organized output folders using zero-byte storage hardlinks. The original files are never duplicated or modified.
- **Explainable Decisions**: Transparent scoring. No black-box AI magic—you can see exactly why a photo was rejected.

---

## Animated Demo

> **[PLACEHOLDER: Animated GIF Demo]**
> *(Recording Guide: Capture a short GIF (15-20 seconds) demonstrating the following flow: 1. Running the pipeline via terminal. 2. Launching the dashboard. 3. Navigating a burst sequence of images. 4. Toggling Scene Intelligence overlays. 5. Reviewing the transparent scoring on a rejected photo. 6. Showing the final hardlinked export folders in the file explorer.)*

## Screenshots

> **[PLACEHOLDER: Main Dashboard Screenshot]**
> *(Capture: The main overview page showing the KEEP/REVIEW/REJECT distribution and a contact sheet of images.)*

> **[PLACEHOLDER: Scene Intelligence Screenshot]**
> *(Capture: The detail view of a single image showing bounding boxes for faces and subjects, with the technical metrics sidebar visible.)*

> **[PLACEHOLDER: Export Folders Screenshot]**
> *(Capture: A file explorer view showing the original `test_datasets` alongside the `output/KEEP`, `output/REVIEW`, and `output/REJECT` directories.)*

---

## Architecture

Local AI Culling operates as a highly modular pipeline. 

```mermaid
graph TD
    A[Image Ingestion] --> B[Technical Analysis]
    B --> C[Duplicate Detection]
    C --> D[Burst Ranking]
    D --> E[Classification]
    E --> F[Scene Intelligence]
    F --> G[Export Engine]
    G --> H[Feedback Dashboard]
    
    subgraph Technical Analysis
    B1(Blur & Focus)
    B2(Composition)
    B3(Subject Quality)
    B4(Face & Eye State)
    B5(Editability Engine)
    end
    B -.-> Technical Analysis
```

## Installation

### Prerequisites
- **Python**: 3.10 or higher.
- **Storage**: SSD highly recommended for fast preview reading.

### Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/local_ai_culling.git
   cd local_ai_culling
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Mac/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Model Placement:**
   Ensure the following models are placed in the `models/` directory:
   - `yolov8n.pt` (Ultralytics YOLOv8)
   - `face_landmarker.task` (MediaPipe FaceLandmarker)

## Usage

### 1. Running the Pipeline
Run the culling engine on a folder of photographs:

```bash
python main.py -i path/to/your/photos -o output
```
This will analyze the photos and create the final `KEEP`, `REVIEW`, and `REJECT` folders via hardlinks.

### 2. Launching the Dashboard
To review the results visually:

```bash
python run_dashboard.py
```
Open your browser to `http://localhost:5000`.

---

## Project Structure

- `core/`: Core data models, pipeline orchestration, and configuration loading.
- `modules/`: Individual AI logic modules (blur, composition, face/eye, editability, duplicate detection).
- `analysis/`: Profiling and performance analysis tools.
- `scoring/`: Rule-based classification logic linking technical scores to final decisions.
- `templates/`: HTML templates for the local web dashboard.
- `utils/`: Shared utilities (image processing, logging).
- `docs/`: In-depth documentation covering architecture, research, and validation phases.
- `models/`: Directory for required machine learning weights (`.pt`, `.task`).
- `output/`: Default directory for hardlinked output and runtime metadata.

---

## Configuration

The software is highly customizable via `config.yml`. Key configurable options include:
- **`thresholds`**: Adjust the strictness for blur, noise, and face quality.
- **`weights`**: Adjust how much different factors (e.g., composition vs focus) contribute to the final score.
- **`export.mode`**: Choose between `hardlink` (default, zero extra storage) or `copy`.
- **`culling.max_burst_time_gap`**: The maximum time gap (in seconds) to consider photos part of the same burst.

---

## Documentation

For a deeper dive into the engineering and design philosophy behind Local AI Culling, see:
- [Implementation Walkthrough](docs/phases/Walkthrough.md)
- [Architecture Proposal](docs/architecture/Architecture.md)
- [Validation Reports](docs/research/Validation_Report.md)

---

## Roadmap

Check out the [ROADMAP.md](ROADMAP.md) for a summary of completed milestones (like Expression Intelligence and the Editability Engine) and a look at our future goals.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
