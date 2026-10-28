<div align="center">

# 🗄️ Docker PostgreSQL & Media Backup Utility

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Compatible-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pg__dump-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Status](https://img.shields.io/badge/Status-Production--Ready-success?style=for-the-badge)]()
[![License](https://img.shields.io/badge/License-MIT-brightgreen?style=for-the-badge)]()

**A lightweight, zero-dependency automation tool for backing up Dockerized PostgreSQL databases and persistent media/upload directories with built-in retention pruning, rotating logs, and desktop error alerts.**

[Features](#-features) • [Installation](#-installation) • [Configuration](#-configuration) • [Usage](#-usage) • [PyInstaller](#-executable-build-pyinstaller) • [Troubleshooting](#-troubleshooting)

</div>

---

## ✨ Features

- 🐘 **Containerized Database Dumps:** Executes live, clean PostgreSQL dumps (`pg_dump --clean`) directly from inside your running Docker container via `docker exec`.
- 📦 **Docker Volume/Uploads Archiving:** Seamlessly pulls media and file upload directories out of Docker containers (`docker cp`) and packages them into timestamped `.zip` archives.
- ⚙️ **Centralized `config.ini`:** No code editing required—manage database targets, container names, backup limits, and upload toggles via an external configuration file.
- 🧊 **PyInstaller Ready:** Designed with dynamic base-path resolution (`sys.frozen` safe) so it works out of the box as a standalone single-binary executable.
- 🔄 **Smart Retention Policy:** Automatically purges older `.sql` and `.zip` files once the retention quota is reached, keeping disk usage under control.
- 🚨 **GUI Failure Alerts:** Fires an instant, topmost `tkinter` desktop error popup if any backup fails, preventing silent automated breakdowns.
- 📜 **Auto-Rotating Logs:** Keeps up-to-date execution history with a 5 MB rotating log handler (`RotatingFileHandler`), preventing log sprawl.

---

## 📂 Project Structure

```text
📁 Project_Root/
├── 📄 main.py                    # Core backup utility
├── ⚙️ config.ini                 # User configuration file
├── 📄 backup_utility.log         # Active runtime log (max 5 MB)
├── 📄 backup_utility.log.1       # Archived log file (when rotated)
├── 📁 Backups/                   # Generated PostgreSQL dumps (.sql)
│   ├── 📜 backup_2026-10-27_02-00-00.sql
│   └── 📜 backup_2026-10-28_02-00-00.sql
└── 📁 Backups_Uploads/           # Generated media/upload archives (.zip)
    ├── 📦 uploads_2026-10-27_02-00-00.zip
    └── 📦 uploads_2026-10-28_02-00-00.zip
```

---

## 📋 Prerequisites

Before running the utility, verify your environment meets the following requirements:

1. **Python 3.8+** (uses only standard library modules—no `pip install` required).
2. **Docker CLI:** Installed, running, and accessible by the current system user without prompts.
3. **Tkinter:** Installed with Python (on headless/Linux environments, install via `sudo apt-get install python3-tk` if GUI alerts are needed).

---

## ⚙️ Configuration

Place a `config.ini` file in the same directory as `main.py` (or adjacent to your compiled executable).

### Example `config.ini`

```ini
[database]
# The name of the running PostgreSQL Docker container
docker_container_name = my_postgres_db

# Database credentials
username = postgres_user
database_name = production_db

[backup]
# Number of newest backups to retain in each directory
max_backups = 5
# Prefix attached to generated .sql files
backup_prefix = backup_

[uploads]
# Set to true to archive uploaded files/media, false to disable
enabled = true
# The container name where the uploads folder lives
container_name = my_web_app
# The absolute path inside the container to archive
container_path = /app/public/uploads
# Prefix attached to generated .zip files
backup_prefix = uploads_
```

### Configuration Options Breakdown

| Section | Key | Type | Description |
| :--- | :--- | :---: | :--- |
| `[database]` | `docker_container_name` | `string` | Target PostgreSQL container name or ID. |
| `[database]` | `username` | `string` | PostgreSQL user used with `pg_dump -U`. |
| `[database]` | `database_name` | `string` | PostgreSQL database name used with `-d`. |
| `[backup]` | `max_backups` | `integer`| Retention count for database files and upload archives. |
| `[backup]` | `backup_prefix` | `string` | Prefix for database backup files (e.g., `backup_`). |
| `[uploads]` | `enabled` | `boolean`| Toggle (`true`/`false`) to enable/disable uploads backup. |
| `[uploads]` | `container_name` | `string` | Name of the container hosting your uploads directory. |
| `[uploads]` | `container_path` | `string` | Container directory path to extract and zip. |
| `[uploads]` | `backup_prefix` | `string` | Prefix for compressed upload archives. |

---

## 🚀 Usage

### Manual Execution

Run the script directly using Python:

```bash
python main.py
```

### Automated Scheduling

#### Linux / macOS (`cron`)
Add an entry to `crontab -e` to run daily at 2:00 AM:
```cron
0 2 * * * cd /path/to/project && /usr/bin/python3 main.py >> /dev/null 2>&1
```

#### Windows (Task Scheduler)
1. Open **Task Scheduler** and select **Create Basic Task**.
2. Set your preferred trigger (e.g., Daily).
3. Action: **Start a program**.
4. Program/script: `pythonw.exe` (or your compiled `.exe`).
5. Arguments: `main.py`
6. Start in: `C:\path\to\project` *(critical so `config.ini` is found)*.

---

## 📦 Executable Build (PyInstaller)

Because the script handles executable base paths dynamically via `sys.frozen`, you can compile it into a standalone executable that runs without requiring Python installed on the target machine:

```bash
# Install PyInstaller
pip install pyinstaller

# Build a single standalone executable (windowed hides the console window on Windows)
pyinstaller --noconfirm --onedir --windowed main.py
```

> **Note:** Always ensure `config.ini` is copied into the same directory as the generated `.exe`.

---

## 📝 Logging & Monitoring

All backup operations, successful cleanups, and process errors are automatically logged to `backup_utility.log`:

```log
2026-10-28 02:00:00 - INFO - === Backup Routine Started ===
2026-10-28 02:00:00 - INFO - Starting Database backup -> backup_2026-10-28_02-00-00.sql...
2026-10-28 02:00:04 - INFO - Database backup finished successfully.
2026-10-28 02:00:04 - INFO - Starting Uploads backup from my_web_app:/app/public/uploads...
2026-10-28 02:00:09 - INFO - Uploads backup finished successfully -> uploads_2026-10-28_02-00-00.zip
2026-10-28 02:00:09 - INFO - Deleting 1 old backups in Backups...
2026-10-28 02:00:09 - INFO - Deleted: backup_2026-10-22_02-00-00.sql
2026-10-28 02:00:09 - INFO - === Backup Routine Ended ===
```

---

## 🛠️ Troubleshooting

<details>
<summary><b>❌ Error: "Missing config file: config.ini"</b></summary>

Ensure `config.ini` exists in the exact same directory as `main.py` (or the built executable). If scheduled via cron or Task Scheduler, make sure the task's "working directory" is set to the project root.
</details>

<details>
<summary><b>❌ Docker permission denied or daemon not running</b></summary>

The executing user must have permission to interact with the Docker daemon. On Linux, ensure the user belongs to the `docker` group:
```bash
sudo usermod -aG docker $USER
```
</details>

<details>
<summary><b>❌ `TclError: no display name and no $DISPLAY environment variable`</b></summary>

This occurs on headless Linux servers where no desktop environment exists. If running strictly headless via cron, wrap the script or launch with a virtual frame buffer like `xvfb-run python main.py`.
</details>

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).