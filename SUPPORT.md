# Support

If you need help with Local AI Culling, please refer to the following resources:

## 1. Documentation
Before opening an issue, please check the extensive internal documentation in the `docs/` folder or the main `README.md`. 
The [Implementation Walkthrough](docs/walkthrough.md) provides an excellent overview of how the pipeline operates under the hood.

## 2. GitHub Issues
If you encounter a bug, crash, or an unexpected AI classification, please open an issue on the GitHub repository. 
When filing a bug report, please include:
- Your Operating System
- Your Python version
- The terminal output or traceback
- A description of the expected behavior vs. actual behavior

## 3. Feedback Dashboard
If the AI is classifying images incorrectly, you can launch the local feedback dashboard (`python run_dashboard.py`) to visually inspect the transparent scores. Often, modifying the strictness variables inside `config.yml` (e.g., `thresholds.blur_threshold`) will resolve your issue without requiring code changes.

## 4. Feature Requests
We welcome feature requests via GitHub Issues. Please tag your issue with `enhancement`. Note that this project prioritizes features that assist professional workflow speed and offline privacy over cloud-dependent or generative AI features.
