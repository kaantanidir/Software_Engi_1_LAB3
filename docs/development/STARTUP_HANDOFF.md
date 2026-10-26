# Startup handoff - 26 October 2026

Saved during a low-battery interruption; resumed and completed after the user connected power.

Completed locally:
- SmartBrew started at http://127.0.0.1:8765/ using the existing database (PID 36016 at launch).
- Added tools/start_smartbrew.ps1: starts/reuses optional Ollama, then starts SmartBrew; -SkipAI omits AI setup; -Port and -Database are supported.
- Updated tools/start_local_ai.ps1: checks installed models, downloads only if missing, supports -NoDownload and -SkipWarmup.
- README documents one-time model setup, combined startup, direct Python startup and the Windows-specific launcher.
- Added the launcher to the submission ZIP whitelist.

Verification completed:
- Both PowerShell scripts parsed without syntax errors.
- Combined and -SkipAI startup served six drinks and exposed the real model on isolated databases.
- Existing Ollama PID 41912 was reused; no model download was triggered, and the live demo stayed available.
- README, architecture, AI-use record and PDF generation instructions were updated for combined startup.
- Report/appendix and the 83-entry ZIP were rebuilt and checked after the changes.

After a laptop restart, run powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_smartbrew.ps1. Servers do not survive shutdown. If the demo is already listening on 8765, use it or choose -Port 8767 rather than launching another app on the same port.

Runtime note: sandboxed Ollama could not read the existing model manifest. Its own PID 16644 was stopped; Ollama was relaunched outside the sandbox. This is an agent-environment permission issue, not evidence of a missing/corrupt model. Check the live status and data/local-ai/server.err.log before changing model files.

The earlier story comparison and 251-message transcript work is saved. No commit/push was made. Do not discard existing changes or include .vs/, data/ or model weights in Git.
