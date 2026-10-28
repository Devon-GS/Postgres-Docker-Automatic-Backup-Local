import sys
import subprocess
import datetime
import os
import shutil
import tempfile
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import logging
from logging.handlers import RotatingFileHandler
import configparser

# --- PyInstaller Safe Base Path ---
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).resolve().parent

# --- Directories & Logs ---
BACKUP_DB_DIR = APP_DIR / "Backups"
BACKUP_UPLOADS_DIR = APP_DIR / "Backups_Uploads"
LOG_FILE = APP_DIR / "backup_utility.log"

# --- Logging Configuration ---
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
logger = logging.getLogger("BackupLogger")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=1)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

# --- Load Configuration (config.ini) ---
CONFIG_FILE = APP_DIR / "config.ini"
config = configparser.ConfigParser()

if not CONFIG_FILE.exists():
    logger.error("config.ini not found.")
else:
    config.read(CONFIG_FILE, encoding="utf-8")

# Database settings
DB_CONTAINER = config.get("database", "docker_container_name", fallback="")
DB_USER = config.get("database", "username", fallback="")
DB_NAME = config.get("database", "database_name", fallback="")

# General backup settings
MAX_BACKUPS = config.getint("backup", "max_backups", fallback=5)
DB_PREFIX = config.get("backup", "backup_prefix", fallback="backup_")

# Uploads settings
UPLOADS_ENABLED = config.getboolean("uploads", "enabled", fallback=False)
UPLOADS_CONTAINER = config.get("uploads", "container_name", fallback="")
UPLOADS_PATH = config.get("uploads", "container_path", fallback="")
UPLOADS_PREFIX = config.get("uploads", "backup_prefix", fallback="uploads_")


def show_error_popup(title, message):
    """Displays a GUI popup for errors."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showerror(title, message)
    root.destroy()


def cleanup_directory(target_dir: Path, pattern: str, limit: int):
    """Keeps only the newest N files matching the pattern in the given directory."""
    files = list(target_dir.glob(pattern))
    files.sort(key=os.path.getmtime)

    if len(files) > limit:
        to_delete = len(files) - limit
        logger.info(f"Deleting {to_delete} old backups in {target_dir.name}...")
        while len(files) > limit:
            old_file = files.pop(0)
            try:
                old_file.unlink()
                logger.info(f"Deleted: {old_file.name}")
            except Exception as e:
                logger.error(f"Failed to delete {old_file.name}: {e}")


def backup_database(timestamp: str):
    """Dumps the PostgreSQL database from Docker."""
    if not all([DB_CONTAINER, DB_USER, DB_NAME]):
        raise ValueError("Missing database settings in config.ini (docker_container_name, username, or database_name)")

    BACKUP_DB_DIR.mkdir(parents=True, exist_ok=True)
    backup_file = BACKUP_DB_DIR / f"{DB_PREFIX}{timestamp}.sql"
    
    command = [
        "docker", "exec", DB_CONTAINER,
        "pg_dump", "-U", DB_USER, "-d", DB_NAME, "--clean"
    ]
    
    logger.info(f"Starting Database backup -> {backup_file.name}...")
    with open(backup_file, "w", encoding="utf-8") as f:
        subprocess.run(command, stdout=f, stderr=subprocess.PIPE, text=True, check=True)
    
    logger.info("Database backup finished successfully.")
    cleanup_directory(BACKUP_DB_DIR, f"{DB_PREFIX}*.sql", MAX_BACKUPS)


def backup_uploads(timestamp: str):
    """Copies the uploads folder from Docker and zips it."""
    if not all([UPLOADS_CONTAINER, UPLOADS_PATH]):
        raise ValueError("Missing uploads settings in config.ini (container_name or container_path)")

    BACKUP_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    zip_dest_base = BACKUP_UPLOADS_DIR / f"{UPLOADS_PREFIX}{timestamp}"
    
    logger.info(f"Starting Uploads backup from {UPLOADS_CONTAINER}:{UPLOADS_PATH}...")

    # Use a temporary folder to hold files copied from docker before compressing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_extracted_path = Path(temp_dir) / "extracted_uploads"
        
        # 1. Copy out of Docker container
        copy_cmd = ["docker", "cp", f"{UPLOADS_CONTAINER}:{UPLOADS_PATH}", str(temp_extracted_path)]
        result = subprocess.run(copy_cmd, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Docker cp failed: {result.stderr.strip()}")

        # 2. Compress the folder to a .zip archive
        shutil.make_archive(str(zip_dest_base), format="zip", root_dir=temp_extracted_path)

    logger.info(f"Uploads backup finished successfully -> {zip_dest_base.name}.zip")
    cleanup_directory(BACKUP_UPLOADS_DIR, f"{UPLOADS_PREFIX}*.zip", MAX_BACKUPS)


def run_all_backups():
    if not CONFIG_FILE.exists():
        msg = f"Missing config file: {CONFIG_FILE.name}\nPlease create it next to the application."
        logger.error(msg)
        show_error_popup("Config Error", msg)
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    errors = []

    # 1. Run Database Backup
    try:
        backup_database(timestamp)
    except subprocess.CalledProcessError as e:
        err = f"Database backup failed:\n{e.stderr.strip() if e.stderr else e}"
        logger.error(err)
        errors.append(err)
    except Exception as e:
        err = f"Database backup error: {e}"
        logger.error(err)
        errors.append(err)

    # 2. Run Uploads Backup (if enabled)
    if UPLOADS_ENABLED:
        try:
            backup_uploads(timestamp)
        except Exception as e:
            err = f"Uploads backup error: {e}"
            logger.error(err)
            errors.append(err)
    else:
        logger.info("Uploads backup is disabled in config.ini. Skipping.")

    # Show alert if anything failed
    if errors:
        show_error_popup("Backup Error", "\n\n".join(errors))


if __name__ == "__main__":
    logger.info("=== Backup Routine Started ===")
    run_all_backups()
    logger.info("=== Backup Routine Ended ===")