# semantic_memory_fs.py

import os
import json
from datetime import datetime, timezone
import uuid
import logging
from typing import Dict, Any, Optional, Union

# --- Configuration & Setup ---
SMFS_BASE_DIR: str = "semantic_memory_storage" # Renamed for clarity
# Create the directory if it doesn't exist.
try:
    os.makedirs(SMFS_BASE_DIR, exist_ok=True)
except OSError as e:
    logging.error(f"Failed to create semantic memory directory {SMFS_BASE_DIR}: {e}", exc_info=True)
    # Depending on the application's criticality, you might raise the exception
    # or have a fallback mechanism. For now, we'll just log.

# Logging configured at application startup
logger = logging.getLogger(__name__)

# --- Functions ---
def save_chain_to_fs(chain_data: Dict[str, Any], sub_directory: Optional[str] = None) -> Optional[str]:
    """
    Saves a reasoning chain as a structured semantic memory object to the filesystem.

    The function ensures the chain has a unique ID and a UTC timestamp.
    It writes the chain data to a JSON file in a predefined directory, optionally within a subdirectory.

    Args:
        chain_data: A dictionary containing the reasoning chain data.
                    If 'id' is not present, a new UUID will be generated.
        sub_directory: Optional. A subdirectory within SMFS_BASE_DIR to save the file.

    Returns:
        The absolute file path (str) where the chain was saved, or None if saving failed.
    """
    try:
        # Ensure 'id' and 'created_at' (or 'timestamp') are set
        chain_id: str = chain_data.get("id") or str(uuid.uuid4())
        chain_data["id"] = chain_id # Ensure the ID used is in the data

        # Use timezone-aware datetime object for UTC for 'created_at' if not present or to standardize
        # If 'timestamp' is used by the kernel, ensure it's also standardized or add 'created_at'
        if "timestamp" not in chain_data or not isinstance(datetime.fromisoformat(chain_data["timestamp"].replace("Z", "+00:00")), datetime):
             chain_data["timestamp_fs_utc"] = datetime.now(timezone.utc).isoformat() # Add a dedicated FS timestamp
        
        # Determine save directory
        current_save_dir = SMFS_BASE_DIR
        if sub_directory:
            current_save_dir = os.path.join(SMFS_BASE_DIR, sub_directory)
            os.makedirs(current_save_dir, exist_ok=True)


        file_name: str = f"reasoning_chain_{chain_id}.json"
        file_path: str = os.path.join(current_save_dir, file_name)
        abs_file_path: str = os.path.abspath(file_path)


        # Atomicity: Write to a temporary file first, then rename.
        temp_file_path: str = abs_file_path + ".tmp"

        with open(temp_file_path, "w", encoding='utf-8') as f:
            json.dump(chain_data, f, indent=4, ensure_ascii=False) # Using indent=4 for better readability

        os.rename(temp_file_path, abs_file_path)

        logger.info(f"Reasoning chain '{chain_id}' saved successfully to '{abs_file_path}'")
        return abs_file_path

    except IOError as e:
        # More specific error logging
        logger.error(f"IOError saving chain '{chain_id if 'chain_id' in locals() else 'unknown_id'}': {e}", exc_info=True)
    except TypeError as e:
        logger.error(f"TypeError during JSON serialization for chain '{chain_id if 'chain_id' in locals() else 'unknown_id'}': {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error saving chain '{chain_id if 'chain_id' in locals() else 'unknown_id'}': {e}", exc_info=True)
    
    # Cleanup temp file if it exists and an error occurred before rename
    if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
        try:
            os.remove(temp_file_path)
            logger.warning(f"Removed temporary file '{temp_file_path}' due to save error.")
        except OSError as e_remove:
            logger.error(f"Failed to remove temporary file '{temp_file_path}': {e_remove}", exc_info=True)
            
    return None

def load_chain_from_fs(uid: str, sub_directory: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Loads a previously saved reasoning chain by its UID from the filesystem.

    Args:
        uid: The unique identifier (str) of the reasoning chain to load.
        sub_directory: Optional. The subdirectory within SMFS_BASE_DIR where the file is located.


    Returns:
        A dictionary (Dict[str, Any]) containing the loaded chain data,
        or None if the file is not found or an error occurs during loading/parsing.
    """
    file_name: str = f"reasoning_chain_{uid}.json"
    current_load_dir = SMFS_BASE_DIR
    if sub_directory:
        current_load_dir = os.path.join(SMFS_BASE_DIR, sub_directory)
        
    file_path: str = os.path.join(current_load_dir, file_name)
    abs_file_path: str = os.path.abspath(file_path)


    if not os.path.exists(abs_file_path):
        logger.warning(f"Reasoning chain file not found for UID '{uid}' at '{abs_file_path}'")
        return None

    try:
        with open(abs_file_path, "r", encoding='utf-8') as f:
            data: Dict[str, Any] = json.load(f)
        logger.info(f"Reasoning chain '{uid}' loaded successfully from '{abs_file_path}'")
        return data
    except FileNotFoundError: # Should be caught by os.path.exists, but good for robustness in case of race conditions
        logger.warning(f"Attempted to load non-existent file (race condition likely) for UID '{uid}' at '{abs_file_path}'")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError loading chain '{uid}' from '{abs_file_path}': Invalid JSON format. {e}", exc_info=True)
        return None
    except IOError as e:
        logger.error(f"IOError loading chain '{uid}' from '{abs_file_path}': {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading chain '{uid}' from '{abs_file_path}': {e}", exc_info=True)
        return None