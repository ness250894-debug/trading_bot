import os
import glob
import logging
import duckdb

logger = logging.getLogger("MigrationManager")

class MigrationManager:
    def __init__(self, conn):
        self.conn = conn
        self.migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')

    def ensure_migration_table(self):
        """Creates the schema_versions table if it doesn't exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_versions (
                version_id INTEGER PRIMARY KEY,
                version_name VARCHAR NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    def get_applied_migrations(self):
        """Returns a set of applied migration names."""
        result = self.conn.execute("SELECT version_name FROM schema_versions").fetchall()
        return {r[0] for r in result}

    def run_migrations(self):
        """Applies all pending migrations in order."""
        self.ensure_migration_table()
        applied = self.get_applied_migrations()
        
        # Get all .sql files in migrations directory
        files = sorted(glob.glob(os.path.join(self.migrations_dir, '*.sql')))
        
        for file_path in files:
            filename = os.path.basename(file_path)
            if filename in applied:
                continue
                
            logger.info(f"Applying migration: {filename}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
                
                # Execute in transaction
                self.conn.begin()
                self.conn.execute(sql_script)
                
                # Record migration
                self.conn.execute(
                    "INSERT INTO schema_versions (version_id, version_name) VALUES ((SELECT COUNT(*) + 1 FROM schema_versions), ?)",
                    [filename]
                )
                self.conn.commit()
                logger.info(f"Successfully applied: {filename}")
                
            except Exception as e:
                self.conn.rollback()
                logger.error(f"Failed to apply migration {filename}: {e}")
                raise e

# Helper to run migrations from CLI if needed
if __name__ == "__main__":
    from app.core.database import DuckDBHandler
    from app.core import config
    
    db = DuckDBHandler(config.DB_PATH)
    conn = db.conn
    mgr = MigrationManager(conn)
    mgr.run_migrations()
    # DuckDBHandler manages connection

