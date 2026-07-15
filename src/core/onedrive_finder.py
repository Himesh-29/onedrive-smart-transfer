"""
OneDrive folder finder.

Detects the OneDrive Personal folder dynamically using environment variables
and common path patterns. Never accesses the Windows registry.
If auto-detection fails, prompts the user to provide the path.
"""

import os
from glob import glob
from typing import Optional


def detect_onedrive_path() -> Optional[str]:
    """Attempt to detect the OneDrive Personal folder path.

    Detection strategy (in order):
      1. Check the 'OneDriveConsumer' environment variable (set by OneDrive for personal accounts).
      2. Check the 'OneDrive' environment variable (generic fallback).
      3. Look for folders matching 'OneDrive*' in the user's profile directory.

    No registry access is performed. No private files are read.

    Returns:
        The detected OneDrive path, or None if detection fails.
    """
    # Strategy 1: OneDriveConsumer env var (most reliable for personal OneDrive)
    onedrive_consumer = os.environ.get("OneDriveConsumer")
    if onedrive_consumer and os.path.isdir(onedrive_consumer):
        return onedrive_consumer

    # Strategy 2: Generic OneDrive env var
    onedrive_generic = os.environ.get("OneDrive")
    if onedrive_generic and os.path.isdir(onedrive_generic):
        return onedrive_generic

    # Strategy 3: Pattern match in user profile directory
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        # Look for folders starting with "OneDrive" in the user profile
        matches = glob(os.path.join(user_profile, "OneDrive*"))
        # Filter to actual directories
        dir_matches = [m for m in matches if os.path.isdir(m)]
        if dir_matches:
            # Prefer exact "OneDrive" match if available
            for match in dir_matches:
                if os.path.basename(match) == "OneDrive":
                    return match
            # Otherwise return the first match
            return dir_matches[0]

    return None


def list_onedrive_subfolders(onedrive_path: str) -> list[dict[str, str]]:
    """List the top-level subfolders inside the OneDrive directory.

    Args:
        onedrive_path: The root OneDrive folder path.

    Returns:
        A list of dicts with 'name' and 'path' keys for each subfolder.
    """
    if not onedrive_path or not os.path.isdir(onedrive_path):
        return []

    subfolders = []
    try:
        for entry in sorted(os.listdir(onedrive_path)):
            full_path = os.path.join(onedrive_path, entry)
            if os.path.isdir(full_path):
                subfolders.append({"name": entry, "path": full_path})
    except OSError:
        pass

    return subfolders
