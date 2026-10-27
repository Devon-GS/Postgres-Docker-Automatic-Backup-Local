# 🗄️ Docker PostgreSQL Backup Utility

![Python Version](https://img.shields.io/badge/python-3.6%2B-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![PostgreSQL](https://img.shields.io/badge/postgres-pg__dump-336791)
![License](https://img.shields.io/badge/license-MIT-green)

An automated, lightweight Python utility designed to securely extract and manage PostgreSQL database backups from a running Docker container. Complete with automated retention policies, rotating logs, and GUI-based error alerts.

---

## ✨ Key Features

* **🐳 Docker-Native:** Seamlessly interfaces with your running Postgres container using `docker exec` and `pg_dump`.
* **🔄 Smart Retention Policy:** Automatically prunes old backups to save disk space (configurable limit, defaults to keeping the latest 5).
* **🚨 GUI Error Alerts:** Utilizes `tkinter` to display immediate, top-level popup notifications if a backup or cleanup process fails.
* **📜 Rotating Logs:** Implements Python's `RotatingFileHandler` to keep a detailed history of backup events without blowing up your storage (max 5MB per log).
* **🧹 Fail-Safe Cleanup:** If a backup fails mid-process, the script automatically detects and cleans up the partial/corrupted `.sql` file.

---

## 📋 Prerequisites

Before running this script, ensure you have the following installed on your host machine:

1. **Python 3.6+** 
2. **Tkinter:** Usually included with Python, but on some Linux distributions, you may need to install it separately (e.g., `sudo apt-get install python3-tk`).
3. **Docker:** Must be installed, running, and the executing user must have permissions to run `docker exec` commands.

---

## ⚙️ Configuration

The script is built to be easily customizable. Open `main.py` and modify the `# --- Configuration ---` block at the top of the file to match your environment:

| Variable | Description | Default Value |
| :--- | :--- | :--- |
| `BACKUP_DIR_NAME` | Folder name where backups will be saved. | `"Backups"` |
| `BACKUP_PREFIX` | Prefix attached to the `.sql` backup files. | `"backup_"` |
| `MAX_BACKUPS` | Maximum number of backup files to retain. | `5` |
| `DOCKER_CONTAINER_NAME`| Name of the target Docker container. | `"sasol-accounting-db-primary"`|
| `USERNAME` | PostgreSQL database user. | `"accounting"` |
| `DATABASE_NAME` | PostgreSQL database name. | `"accounting"` |

---

## 🚀 Usage

Simply run the script using Python. You can run this manually, or set it up as a cron job/scheduled task for fully automated backups.

```bash
python main.py
```

### 📂 Directory Output

After a successful run, your project directory will look like this:

```text
📁 Project_Root/
├── 📄 main.py                  # The backup script
├── 📄 backup_utility.log       # Rotating log file (up to 5MB)
├── 📄 backup_utility.log.1     # Archived log file (if rotation occurs)
└── 📁 Backups/                 # Auto-generated backup directory
    ├── 📜 backup_2026-10-25_14-00-00.sql
    ├── 📜 backup_2026-10-26_14-00-00.sql
    └── 📜 backup_2026-10-27_14-00-00.sql
```

---

## 📝 Logging & Monitoring

The script logs all activity to `backup_utility.log`. 
* **Successes:** Logs the start, completion, and automated deletion of old backups.
* **Failures:** Captures specific Docker `stderr` outputs and logs the exact exit codes. 
* *Note: If a critical error occurs, a GUI message box will pop up on the host screen to ensure the failure doesn't go unnoticed.*

---

## 🛠️ Troubleshooting

* **`tkinter._tkinter.TclError: no display name and no $DISPLAY environment variable`**
  * *Cause:* You are running the script on a headless server (no GUI). 
  * *Fix:* If you are running this on a headless Linux server via Cron, you may need to disable the `tkinter` popup feature or map it to a virtual display like `Xvfb`.
* **`subprocess.CalledProcessError: Command '['docker', 'exec', ...]`**
  * *Cause:* Docker is not running, the container name is incorrect, or the user lacks permissions.
  * *Fix:* Ensure Docker is running and verify `DOCKER_CONTAINER_NAME` matches your active container (`docker ps`).

***