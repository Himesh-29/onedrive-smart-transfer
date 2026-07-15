---
name: Thread-Safe UI Updates
description: Guidelines for updating the customtkinter UI from background threads safely.
---

# Thread-Safe UI Updates

**Context**: The application uses a background worker thread (`TransferEngine`) to avoid blocking the main `customtkinter` thread.

**Rules**:
- The AI MUST NEVER update `customtkinter` widgets directly from the `TransferEngine` worker thread.
- Instead, read from `engine.progress_queue` using a scheduled `.after(100, update_ui_method)` loop in the main thread (e.g., in `transfer_queue.py`).
- Always check if the application is shutting down before scheduling another `.after` callback.
