---
name: Transfer Engine Error Handling
description: Guidelines for handling OS errors during file transfers.
---

# Transfer Engine Error Handling

**Context**: The `TransferEngine` executes actual file copies/moves using `shutil`.

**Rules**:
- Wrap all file operations (`os.makedirs`, `shutil.copy2`, `shutil.move`) in `try...except OSError`.
- You must respect the `_skip_all_errors` flag.
- When an error occurs, emit `TransferState.ERROR` to the progress queue.
- Wait for user input (Retry/Skip/Skip All) via `_error_response_queue`. Do not assume automatic skipping unless `_skip_all_errors` is True.
