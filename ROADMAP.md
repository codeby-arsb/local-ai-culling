# Local AI Culling: Roadmap

This document outlines the high-level milestones we have accomplished to bring this software to Version 1.0.0, as well as the future goals for subsequent releases.

## Completed Milestones (Version 1.0.0)

- [x] **Technical Foundation**: Build the core pipeline to evaluate blur, focus, composition, and noise.
- [x] **Burst & Duplicate Logic**: Intelligently group identical frames and select the optimal shot in a high-speed sequence.
- [x] **Image Editability Engine**: Measure the theoretical editability of a RAW file by simulating shadow/highlight recovery and penalizing noise/color degradation.
- [x] **Expression Intelligence**: Introduce semantic understanding of faces (e.g., closed eyes vs. blinking vs. awkward mouth shapes).
- [x] **Zero-Byte Export**: Introduce a hardlink-based export engine to organize `KEEP`, `REVIEW`, and `REJECT` folders instantly on the same storage volume.
- [x] **Feedback Dashboard**: Launch a local web server to visually audit AI decisions and tweak confidence thresholds.
- [x] **Production Hardening**: Optimize the internal caching architecture, reduce disk I/O, and strip legacy components.

## Future Goals (Version 1.x / 2.0)

While Version 1.0.0 provides a complete end-to-end workflow, we are actively researching the following enhancements:

- [ ] **Multi-Camera Sync**: Grouping and comparing images taken from different cameras at the exact same timestamp (useful for second-shooter event photography).
- [ ] **Subject Identity Persistence**: (Optional feature) Recognizing the VIPs (e.g., the bride and groom) and adjusting scoring weights to favor their visibility across a shoot.
- [ ] **GPU Acceleration via ONNX**: Expanding beyond CPU-bound inference for YOLO and MediaPipe by offering robust GPU acceleration wrappers for NVIDIA CUDA and Apple Silicon.
- [ ] **Lightroom Classic Plugin Integration**: Automatically pushing the KEEP/REVIEW/REJECT flags directly into a Lightroom catalog via a lightweight bridge plugin, skipping the hardlink folder structure entirely for users who prefer a single monolithic catalog.

*Note: As a privacy-first, locally-run application, any future feature involving facial identity or metadata analysis will remain 100% offline and strictly opt-in.*
