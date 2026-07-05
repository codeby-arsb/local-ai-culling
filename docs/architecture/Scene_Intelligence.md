# Phase 5E Proposal: Feedback Collection System

To systematically collect data on disagreements between AI Classification and Photographer Judgement without introducing new learning mechanisms, we need a lightweight, frictionless workflow. 

Because photographers have established muscle memory for culling, I propose two different architectural directions. Both remain 100% local, require no internet, and respect privacy by keeping all data within the `local_ai_culling` directory.

---

## Option A: The XMP Sync (Seamless Workflow Integration)

This approach integrates directly into your existing professional tools (Lightroom, Capture One, Photo Mechanic) so you don't have to change how you cull.

**Architecture:**
1.  **Tagging:** After the AI finishes its analysis, it writes `.xmp` sidecar files (or updates EXIF) for the source images, applying color labels (e.g., Green = KEEP, Red = REJECT).
2.  **Native Culling:** You open the folder in your standard culling software. You visually inspect the photos. If you disagree with the AI, you simply change the color label or star rating using your normal keyboard shortcuts.
3.  **Sync & Interview:** When you finish, you run a script `python sync_feedback.py`. 
    - The script reads the updated `.xmp` files and compares them against the original `classification.csv` baseline.
    - If it detects a disagreement (e.g., AI said KEEP, but XMP says REJECT), it triggers a quick terminal prompt:
      `"A7R4 (2475) was KEEP, but you marked REJECT. Reason?: "`
    - You type "Excessive Noise", and the script logs it to a local `disagreements.csv` file.

**Pros:** You get to cull using the industry-standard software you already know and love. It handles RAW files natively.
**Cons:** Requires writing/reading `.xmp` sidecar files.

---

## Option B: Local Web Dashboard (The Dedicated Interface)

This approach builds a dedicated, lightweight interface specifically designed for rapid feedback collection using the preview JPEGs.

**Architecture:**
1.  **Local Server:** A tiny Python `FastAPI` or `Flask` server spins up locally on your machine (e.g., `http://localhost:8000`). It is fully offline.
2.  **Web Interface:** You open the address in your browser. The interface displays your generated preview JPEGs in a clean gallery view.
3.  **Frictionless Interaction:**
    - Each photo displays the AI's classification badge (KEEP, REVIEW, REJECT).
    - You can use arrow keys to navigate and press `K`, `R`, or `V` to override the AI.
    - If you override a decision, a small text box instantly appears below the photo asking for the "Reason" (with an auto-complete dropdown of common reasons like "Closed Eyes", "Distracting Background", etc.).
4.  **Local Database:** All feedback is instantly appended to a local `outputs/photographer_feedback.csv` file.

**Pros:** Extremely tailored, frictionless UI. No messy XMP sidecar files. Great for rapid validation of the preview dataset.
**Cons:** You are culling in a browser using JPEGs instead of your native editing software.

---

## Deliverables & Data Structure

Regardless of which option you choose, the resulting deliverable will be a pristine `outputs/photographer_feedback.csv` containing:

| Filename | AI_Classification | Photographer_Decision | Reason | Mathematical_Score |
| :--- | :--- | :--- | :--- | :--- |
| A7R4 (2475).jpg | KEEP | REJECT | Excessive Noise | 64.2 |
| A7R4 (2486).jpg | KEEP | REJECT | Closed Eyes | 81.2 |
| SNX02364.JPG | KEEP | REJECT | Foreground Distraction | 75.3 |

This dataset will become the ultimate ground-truth for identifying exactly where the AI's mathematical logic diverges from human aesthetics.

---

## Recommendation

For purely validating the AI logic without disturbing your professional workspace, **Option B (Local Web Dashboard)** is highly recommended. It allows us to build an interface explicitly tailored to gathering the exact `Reason` string effortlessly, without worrying about Lightroom catalog synchronization issues. 

However, if you strongly prefer to do your visual validation inside your professional culling software, **Option A** is the best path.
