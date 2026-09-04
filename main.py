import subprocess
import datetime
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import logging
from logging.handlers import RotatingFileHandler

# --- Configuration ---
BACKUP_DIR_NAME = "Backups"
if not os.path.isdir(BACKUP_DIR_NAME):
    os.makedirs(BACKUP_DIR_NAME)
    
BACKUP_DIR = Path(BACKUP_DIR_NAME) 
# Prefix for the backup files
BACKUP_PREFIX = "backup_"
# Number of backups to keep
MAX_BACKUPS = 5

# --- Logging Configuration ---
LOG_FILE = "backup_utility.log"
MAX_LOG_SIZE = 5 * 1024 * 1024 # 5 MB limit
BACKUP_LOG_COUNT = 1 # Keep 1 old log file (backup_utility.log.1) when it rotates

# Set up the rotating logger
logger = logging.getLogger("BackupLogger")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_LOG_COUNT)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

def show_error_popup(title, message):
    """Displays a GUI popup for errors."""
    root = tk.Tk()
    root.withdraw() # Hide the main, empty window
    root.attributes("-topmost", True) # Force the popup to the front
    messagebox.showerror(title, message)
    root.destroy()

def run_backup():
    # 1. Generate the filename with the current date (e.g., backup_2026-09-03.sql)
    current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = BACKUP_DIR / f"{BACKUP_PREFIX}{current_date}.sql"
    
    # 2. Define the Docker command
    command = [
        "docker", "exec", "-i", "sasol-accounting-db-primary",
        "pg_dump", "-U", "accounting", "-d", "accounting", "--clean"
    ]
    
    logger.info(f"Starting backup: {backup_filename}...")
    
    try:
        # 3. Execute the command and write the output directly to the file
        # Added stderr=subprocess.PIPE to capture exact database errors for the logs/popups
        with open(backup_filename, "w", encoding="utf-8") as backup_file:
            result = subprocess.run(command, stdout=backup_file, stderr=subprocess.PIPE, text=True, check=True)
        logger.info("Backup completed successfully.")
        
    except subprocess.CalledProcessError as e:
        # Extract the specific error output from Docker/pg_dump
        stderr_output = e.stderr.strip() if e.stderr else "No specific error output provided."
        error_msg = f"Command failed with exit code {e.returncode}:\n{stderr_output}"
        
        logger.error(error_msg)
        show_error_popup("Backup Failed", error_msg)
        
        # If the backup failed, delete the empty/partial file
        if backup_filename.exists():
            backup_filename.unlink()
            logger.info(f"Deleted partial/failed backup file: {backup_filename}")
        return
        
    except Exception as e:
        error_msg = f"An unexpected error occurred:\n{e}"
        logger.error(error_msg)
        show_error_popup("Unexpected Error", error_msg)
        return

    # 4. Enforce the retention policy (Keep only 12 backups)
    cleanup_old_backups()

def cleanup_old_backups():
    # Find all files matching the backup prefix and extension
    search_pattern = f"{BACKUP_PREFIX}*.sql"
    backups = list(BACKUP_DIR.glob(search_pattern))
    
    # Sort files by creation/modification time (oldest first)
    backups.sort(key=os.path.getmtime)
    
    # Check if we have more than the allowed maximum
    if len(backups) > MAX_BACKUPS:
        backups_to_delete = len(backups) - MAX_BACKUPS
        logger.info(f"Found {len(backups)} backups. Deleting the oldest {backups_to_delete}...")
        
        # Delete the oldest files until we are down to MAX_BACKUPS
        while len(backups) > MAX_BACKUPS:
            oldest_backup = backups.pop(0) # Remove the first (oldest) from the list
            try:
                oldest_backup.unlink()
                logger.info(f"Deleted old backup: {oldest_backup.name}")
            except Exception as e:
                error_msg = f"Failed to delete {oldest_backup.name}:\n{e}"
                logger.error(error_msg)
                show_error_popup("Cleanup Error", error_msg)
    else:
        logger.info(f"Total backups currently stored: {len(backups)} (Limit: {MAX_BACKUPS})")

if __name__ == "__main__":
    logger.info("--- Backup script triggered ---")
    # Ensure the backup directory exists
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    run_backup()