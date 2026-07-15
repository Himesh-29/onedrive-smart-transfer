# OneDrive Smart Transfer - Global Rules

**Name**: OneDrive Smart Transfer
**Goal**: A free, open-source, offline-only Windows desktop application for transferring project files to OneDrive while automatically excluding bloated build artifacts.
**Tech Stack**: Python, `customtkinter` (for UI), `threading` & `queue` (for background processing).

## 🛑 Core Agent Rules (Critical for AI)
1. **100% Offline**: Do not introduce any network calls, telemetry, or analytics (e.g., `requests`, `urllib`).
2. **No File Content Reading**: Only file/directory *names* and sizes should be inspected. Never read file contents.
3. **Non-Blocking UI**: Any intensive tasks MUST run in background threads using `queue.Queue` to communicate with the `customtkinter` main thread.
4. **Privacy First**: No registry access; use environment variables or explicit user selection for detecting OneDrive.

For architectural details, see `references/architecture.md`.
For recent context and chat history, see `references/history.md`.
