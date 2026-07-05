# Phase 6B: Eye-State Detection & AI Inspector Mode

This implementation plan details the engineering steps to complete **Phase 6B**, including the foundational architecture for the new **AI Inspector Mode**.

## 1. AI Inspector Mode Architecture
To support independent overlay visualization with zero overhead on the dashboard, we will introduce a side-car JSON architecture for spatial metadata.

*   **Pipeline Export:** A new module at the very end of the pipeline will take `record.subject_boxes` and `record.face_boxes` (plus future landmarks/masks) and write them to `output/inspector/[filename].json`.
    *   *Schema Example:* 
        ```json
        {
          "boxes": [
             {"type": "subject", "coords": [x1, y1, x2, y2], "confidence": 0.95},
             {"type": "face", "coords": [x1, y1, x2, y2], "confidence": 0.88}
          ],
          "landmarks": [...] 
        }
        ```
*   **Backend Support:** Update `modules/feedback_server.py` with an endpoint `GET /api/inspector/{filename}` that returns this JSON.
*   **Frontend Rendering:** Update `index.html` to fetch this spatial data when loading an image, and dynamically render absolute-positioned SVG bounding boxes or dots over the main image based on the enabled toggle checkboxes.

## 2. Eye-State & Expression Detection (MediaPipe)
We will transition `modules/face_eye.py` to utilize **MediaPipe Face Mesh** instead of (or alongside) YOLOv8-face, as MediaPipe provides 468 precise 3D facial landmarks which are essential for eye analysis.

*   **Action:** Add `mediapipe` to `requirements.txt`.
*   **Math (EAR & MAR):**
    *   Using the specific landmark indices for the upper and lower eyelids, we will calculate the **Eye Aspect Ratio (EAR)**. If EAR drops below a calibrated threshold (e.g., `< 0.20`), `eyes_closed_confidence` spikes towards 1.0.
    *   Using the lip landmarks, we will calculate the **Mouth Aspect Ratio (MAR)** to capture wide-open mouths, contributing to a baseline `expression_score`.
*   **Data Models:** 
    *   Update `face_eye.py` to accurately export all `face_boxes` (currently missing from array) and the new 468 `landmarks` into the `ImageRecord` so the Inspector Mode can visualize them.
    *   Export `eyes_closed_confidence` to `classification.csv` for transparency.

## 3. Classification Engine Update
*   **Action:** Modify `modules/classification.py`.
*   **Logic:** If `AppConfig.get("modules.eye_state", True)` is enabled, the classifier will aggressively penalize images where `eyes_closed_confidence > 0.80`, forcing them into `REJECT` (or `REVIEW` if they are the absolute best frame in a burst).
*   **Confidence Aggregation:** The confidence engine will be updated to lower the final `confidence_score` if an eye-state penalty triggered a demotion.

## 4. Configuration
*   **Action:** Add the following to `config.yml`:
    ```yaml
    eye_state:
      enabled: true
      ear_threshold: 0.20
      rejection_confidence: 0.80
    ```

---

> [!IMPORTANT]
> **User Review Required**
> Does the side-car JSON architecture for the AI Inspector Mode align with your vision? Separating spatial data into `.json` files keeps the CSVs clean and prevents performance bottlenecks during culling.
> 
> Once approved, I will begin by building the Inspector framework first, then implement MediaPipe to visualize the landmarks in real-time.
