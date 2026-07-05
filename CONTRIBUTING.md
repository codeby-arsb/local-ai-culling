# Contributing to Local AI Culling

Thank you for your interest in contributing! Since this project is built for professional photographers to rely on in their daily workflow, our primary focus is on **stability, performance, and explainability**.

## How to Contribute

1. **Bug Reports & Feature Requests**: Please use the GitHub Issues tab to report any unexpected crashes, AI misclassifications, or UI bugs. Provide as much detail as possible, including OS version and Python version.
2. **Pull Requests**:
   - Create a feature branch from `master`.
   - Ensure you do not commit any generated runtime outputs (`output/`, `logs/`, `cache/`, `metadata/`).
   - Write clear, concise commit messages.
   - Maintain our philosophy of **Explainable AI**: Any new metric or analysis module must output clear reasons for its scores. Avoid "black box" decisions.

## Development Setup

1. Clone the repository and set up a virtual environment.
2. Install dependencies via `pip install -r requirements.txt`.
3. Read the [Implementation Walkthrough](docs/walkthrough.md) to understand the internal pipeline architecture (Ingestion -> Technical Analysis -> Duplicate/Burst -> Classification -> Export).

We welcome contributions particularly in performance optimizations, new scene intelligence recognizers, and UX improvements to the local dashboard.
