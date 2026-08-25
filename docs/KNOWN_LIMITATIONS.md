# Known Limitations - Version 1.0

This document outlines the current known limitations, intentionally postponed features, and technical constraints of Version 1.0. This serves as a reference for users and a roadmap for future v1.x and v2.0 enhancements.

## 1. Supported Image Formats
- **Currently Supported:** .jpg, .jpeg, .png, and standard .CR2/.NEF raw formats.
- **Limitation:** Advanced modern RAW formats (like .CR3, .ARW compressed, or .HEIC) may lack full support or metadata extraction depending on the underlying OS libraries and rawpy version capabilities.
- **Future Roadmap:** Expansion to native .HEIC and expanded RAW support in v1.1.

## 2. Dataset Size & Memory Usage
- **Recommended Size:** Best performance is achieved with sets of 500 to 2,000 images per run. 
- **Limitation:** Because the pipeline performs duplicate detection globally across the entire dataset (via perceptual hashing), memory usage grows non-linearly. Datasets exceeding 5,000 images may experience significant memory pressure and slower duplicate processing.
- **Future Roadmap:** Implementing batched or chunked perceptual hash comparisons for infinite-scale datasets (v1.x).

## 3. Hardware Requirements
- **Current State:** Platform-neutral processing with native Apple Silicon (arm64 / ARM NEON / MPS) and Windows/Linux (x86_64 / CUDA) compatibility.
- **Performance:** On Apple Silicon M-series processors, the full AI quality pipeline processes images at ~60–85ms per image. On older dual-core processors, processing times may average ~300ms–800ms.
- **Future Roadmap:** Formal batch-level GPU/MPS acceleration profiles for multi-image concurrency (v2.0).

## 4. Workflow Constraints
- **Session Persistence:** Currently, closing the dashboard and terminating the local server clears the immediate UI state. Although metadata and CSVs are permanently saved on disk, the UI does not dynamically "reload" a past state if the backend is reset.
- **Destructive Culling:** The engine outputs hardlinks to KEEP/REVIEW/REJECT folders. It does not natively edit Lightroom catalogs (.lrcat) or generate XMP sidecar rating files.

## 5. AI Detection Boundaries
- **Composition:** The Rule of Thirds analyzer currently only detects human subjects. It does not rank architectural or landscape composition.
- **Duplicate Detection (Burst):** High-speed sports photography or heavy continuous shooting where subjects move significantly between frames might falsely split a single burst into multiple unique groups. The temporal threshold is currently hard-coded.
- **Editability Engine:** Only evaluates luminance clipping (blown highlights / crushed shadows). It does not yet evaluate extreme white balance shifts or color channel clipping.

## 6. Intentionally Postponed Features
- Lightroom Classic Plugin integration.
- Custom threshold tuning UI sliders (currently thresholds are static in config.yml).
- Video file culling.
