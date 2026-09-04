import subprocess
import datetime
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

# --- Configuration ---
if not os.path.isdir("Backups"):
    os.makedirs("Backups")
    
BACKUP_DIR = Path("Backups") 
# Prefix for the backup files
BACKUP_PREFIX = "backup_"
# Number of backups to keep
MAX_BACKUPS = 12

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
    
    print(f"Starting backup: {backup_filename}...")
    
    try:
        # 3. Execute the command and write the output directly to the file
        with open(backup_filename, "w") as backup_file:
            subprocess.run(command, stdout=backup_file, check=True)
        print("Backup completed successfully.")
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Error during backup execution:\n{e}"
        print(error_msg)
        show_error_popup("Backup Failed", error_msg)
        
        # If the backup failed, delete the empty/partial file
        if backup_filename.exists():
            backup_filename.unlink()
        return
        
    except Exception as e:
        error_msg = f"An unexpected error occurred:\n{e}"
        print(error_msg)
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
        print(f"Found {len(backups)} backups. Deleting the oldest {backups_to_delete}...")
        
        # Delete the oldest files until we are down to MAX_BACKUPS
        while len(backups) > MAX_BACKUPS:
            oldest_backup = backups.pop(0) # Remove the first (oldest) from the list
            try:
                oldest_backup.unlink()
                print(f"Deleted old backup: {oldest_backup.name}")
            except Exception as e:
                error_msg = f"Failed to delete {oldest_backup.name}:\n{e}"
                print(error_msg)
                show_error_popup("Cleanup Error", error_msg)
    else:
        print(f"Total backups currently stored: {len(backups)} (Limit: {MAX_BACKUPS})")

if __name__ == "__main__":
    # Ensure the backup directory exists
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    run_backup()