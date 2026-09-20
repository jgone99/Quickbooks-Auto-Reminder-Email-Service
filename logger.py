import logging
from datetime import datetime
from pathlib import Path

def cleanup_old_logs(keep: int = 10):
    logs_dir = Path("logs")
    logs_files = sorted(logs_dir.glob("run*.log"))

    if len(logs_files) > keep:
        files_to_delete = logs_files[:-keep]
        for file in files_to_delete:
            file.unlink()

def setup_logging():
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    log_path = logs_dir / f"run_{timestamp}.log"

    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)

    cleanup_old_logs()