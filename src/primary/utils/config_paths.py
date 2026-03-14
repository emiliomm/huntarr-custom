#!/usr/bin/env python3
"""
Path configuration for Huntarr
Handles cross-platform path resolution for Windows, Linux, and macOS
"""

import os
import sys
import pathlib
import tempfile
import platform
import time

# Determine operating system
OS_TYPE = platform.system()  # 'Windows', 'Darwin' (macOS), or 'Linux'

# Get configuration directory
CONFIG_DIR = os.environ.get("HUNTARR_CONFIG_DIR")

if not CONFIG_DIR:
    # Windows default (primary option now that Docker is removed)
    CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Huntarr")

# Initialize the directory structure
CONFIG_PATH = pathlib.Path(CONFIG_DIR)

# Try to create the directory if it doesn't exist
try:
    CONFIG_PATH.mkdir(parents=True, exist_ok=True)
    
    # Define only the directories we actually use
    LOG_DIR = CONFIG_PATH / "logs"
    
    # Create essential directories
    LOG_DIR.mkdir(exist_ok=True)
    
    print(f"Using configuration directory: {CONFIG_DIR}")
    # Check write permissions with a test file
    test_file = CONFIG_PATH / f"write_test_{int(time.time())}.tmp"
    with open(test_file, "w") as f:
        f.write("test")
    if test_file.exists():
        test_file.unlink()  # Remove the test file
except Exception as e:
    print(f"Warning: Could not create or write to config directory at {CONFIG_DIR}: {str(e)}")
    # Fall back to temp directory as last resort
    temp_base = tempfile.gettempdir()
    CONFIG_DIR = os.path.join(temp_base, f"huntarr_config_{os.getpid()}")
    CONFIG_PATH = pathlib.Path(CONFIG_DIR)
    CONFIG_PATH.mkdir(parents=True, exist_ok=True)
    print(f"Using temporary config directory: {CONFIG_DIR}")
    
    # Write to Huntarr logs (not Desktop) for visibility in case of issues
    try:
        log_dir = CONFIG_PATH / "logs"
        log_dir.mkdir(exist_ok=True)
        error_log = log_dir / "huntarr_error.log"
        with open(error_log, "a") as f:
            f.write(f"\nUsing temporary config directory: {CONFIG_DIR}\n")
            f.write(f"Original error accessing primary config: {str(e)}\n")
    except Exception:
        pass

# Create standard directories - only the ones we actually use
LOG_DIR = CONFIG_PATH / "logs"

# Create all directories
for dir_path in [LOG_DIR]:
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create directory {dir_path}: {str(e)}")

# Set environment variables for backwards compatibility
os.environ["HUNTARR_CONFIG_DIR"] = str(CONFIG_PATH)
os.environ["CONFIG_DIR"] = str(CONFIG_PATH)  # For backward compatibility


# Legacy JSON config path functions removed - all settings now stored in database
# Reset file functions removed - all reset requests now stored in database


def ensure_directories() -> None:
    """Ensure config and logs directories exist. Used by Windows service startup."""
    CONFIG_PATH.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
