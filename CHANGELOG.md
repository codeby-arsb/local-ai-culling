# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-14

Version 1.0.0 represents the consolidation of all internal development phases (Phases 1 through 8) into the first public-quality Release Candidate. The software has evolved from a proof-of-concept into a robust, production-ready tool.

### Added
- **Core Culling Engine**: Complete offline pipeline for evaluating technical quality (blur, noise, focus).
- **Duplicate Detection**: Grouping visually identical frames.
- **Burst Ranking**: Automatically identifying high-speed sequences and extracting the single best frame.
- **Expression Intelligence (Phase 6D)**: Semantic facial evaluation detecting blinks, awkward mouth shapes, and occlusion without penalizing subjective artistic expressions (e.g., smiling vs. neutral).
- **Image Editability Engine (Phase 6C)**: Simulation of shadow/highlight recovery on RAW previews to penalize underlying color degradation and noise, ensuring only highly-editable photos are recommended.
- **Scene Intelligence**: Context-aware evaluations recognizing environments like weddings or low-light portraits.
- **Photographer Feedback Dashboard**: A fully local web interface for interactive review and validation of AI decisions.
- **Hardlink Export Engine (Phase 7)**: Zero-byte storage hardlinking that instantly builds `KEEP`, `REVIEW`, and `REJECT` folders without copying or moving the original RAW files.
- **Explainable Decisions**: Transparent metadata tagging allowing users to see exactly why the pipeline classified a photo into its respective category.

### Changed
- **Pipeline Architecture**: Transitioned to a transient image caching model to eliminate redundant disk reads across independent analysis modules, reducing disk I/O by 71% (Phase 8).
- **Documentation**: Completely overhauled project documentation, architecture diagrams, and contribution guidelines for public release.
- **Rule-Based Classification**: Calibrated to a "penalty-only" philosophy for complex features like Editability and Expression, ensuring the AI strictly flags objective technical flaws rather than replacing the photographer's subjective artistic judgment.

### Removed
- **Legacy Code**: Removed outdated EAR (Eye Aspect Ratio) implementations, experimental recovery algorithms, and unused dashboard API endpoints.
- **Silent Failures**: Stripped out silent exception handlers in favor of structured error logging and robust fallbacks to `REVIEW` state.
