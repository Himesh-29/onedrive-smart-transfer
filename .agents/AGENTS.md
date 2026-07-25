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

## 🌳 Git & Branching Rules
1. **Never Force Push**: Never use `git push -f` or force push under any circumstances. If a commit needs to be amended and has already been pushed, create a new commit instead or let the user handle it.
2. **Never Push to Main Directly**: Always follow the PR (Pull Request) workflow. Commit to a feature branch, push the feature branch, and let the user review and merge via PR. Do not `git push origin main` directly.
