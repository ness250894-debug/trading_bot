import shutil
import os
from datetime import datetime
import logging

logger = logging.getLogger("Backup")

# Configuration
DB_FILE = "data/trading_bot.duckdb"
BACKUP_DIR = "backups"

def create_backup():
    """Creates a timestamped backup of the DuckDB database file."""
    try:
        # Ensure backup directory exists
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
            logger.info(f"Created backup directory: {BACKUP_DIR}")

        # Check if DB file exists
        if not os.path.exists(DB_FILE):
            logger.error(f"Database file not found at: {DB_FILE}")
            return False

        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"trading_bot_backup_{timestamp}.duckdb"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)

        # Copy file
        shutil.copy2(DB_FILE, backup_path)
        
        # Verify backup size
        original_size = os.path.getsize(DB_FILE)
        backup_size = os.path.getsize(backup_path)
        
        if original_size == backup_size:
            logger.info(f"✅ Backup successful: {backup_path} (Size: {backup_size/1024/1024:.2f} MB)")
            return True
        else:
            logger.error(f"❌ Backup failed: Size mismatch (Original: {original_size}, Backup: {backup_size})")
            return False

    except Exception as e:
        logger.error(f"❌ Backup failed with error: {e}")
        return False
