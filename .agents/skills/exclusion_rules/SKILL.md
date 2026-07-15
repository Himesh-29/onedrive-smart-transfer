---
name: Exclusion Pattern Management
description: Guidelines for adding or modifying tech-stack exclusion rules.
---

# Exclusion Pattern Management

**Context**: Exclusions are layered. Base defaults are in `config/default_exclusions.json`, and user overrides are saved persistently by `ExclusionManager`.

**Rules**:
1. When adding support for a new tech stack (e.g., a new language):
   - Modify `config/default_exclusions.json` to add the marker file and exclusion patterns.
   - Ensure `stack_detector.py` is updated to recognize the new marker files.
2. Maintain backward compatibility with existing `user_overrides` dict structures in `exclusion_manager.py`.
3. Use `fnmatch` logic for patterns; treat user-added strings without wildcards as directory names.
