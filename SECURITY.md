# Security Policy

Local AI Culling is designed with a **privacy-first, offline-first** architecture.

## Privacy & Offline Execution

This software operates 100% locally on your own hardware. 
- **No images are ever uploaded** to external servers.
- **No cloud APIs** are utilized for image processing or metadata analysis.
- **No usage telemetry** is collected or transmitted.

Because all analysis (including deep-learning inference) happens entirely on your machine, your client's data remains completely private.

## Reporting a Vulnerability

While the application runs strictly offline and does not expose a public server, if you discover any security vulnerabilities (e.g., arbitrary code execution via crafted image files, directory traversal in the local web dashboard), please report them.

Given the private nature of the repository, you can report vulnerabilities by opening an issue on GitHub or reaching out to the maintainer directly. All security issues will be treated as high priority.
