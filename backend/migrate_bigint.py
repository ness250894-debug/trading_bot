#!/usr/bin/env python3
"""
One-time migration script to fix user_id column types from INTEGER to BIGINT.
This should be run once on the production database to fix the schema mismatch.
"""

import duckdb
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_database(db_file="data/trading_bot.duckdb"):
    """Migrate user_id columns from INTEGER to BIGINT."""
    try:
        logger.info(f"Connecting to database: {db_file}")
        conn = duckdb.connect(db_file, read_only=False)
        
        tables_to_migrate = [
            'user_strategies', 'api_keys', 'audit_log', 'subscriptions', 
            'payments', 'trades', 'backtest_results'
        ]
        
        for table in tables_to_migrate:
            try:
                # Check if table exists
                table_exists = conn.execute(
                    "SELECT count(*) FROM information_schema.tables WHERE table_name = ?", 
                    [table]
                ).fetchone()[0] > 0
                
                if not table_exists:
                    logger.info(f"Table {table} does not exist, skipping...")
                    continue
                
                # Check current column type
                col_info = conn.execute(
                    "SELECT data_type FROM information_schema.columns WHERE table_name = ? AND column_name = ?",
                    [table, 'user_id']
                ).fetchone()
                
                if not col_info:
                    logger.info(f"Table {table} has no user_id column, skipping...")
                    continue
                
                current_type = col_info[0]
                logger.info(f"Table {table}.user_id is currently {current_type}")
                
                if current_type == 'BIGINT':
                    logger.info(f"Table {table}.user_id is already BIGINT, skipping...")
                    continue
                
                # Perform migration by creating new table
                logger.info(f"Migrating {table}...")
                
                # Get all columns EXCEPT user_id
                columns = conn.execute(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name != 'user_id'
                    ORDER BY ordinal_position
                """).fetchall()
                
                # Build CREATE TABLE statement with BIGINT for user_id
                create_cols = []
                for col_name, col_type in columns:
                    create_cols.append(f"{col_name} {col_type}")
                
                # Insert user_id as BIGINT at position 2 (after id)
                create_cols.insert(1, "user_id BIGINT")
                
                # Create new table
                conn.execute(f"CREATE TABLE {table}_new AS SELECT * FROM {table} WHERE 1=0")
                
                # Alter user_id to BIGINT
                conn.execute(f"ALTER TABLE {table}_new ALTER COLUMN user_id TYPE BIGINT")
                
                # Copy data
                logger.info(f"Copying data from {table} to {table}_new...")
                conn.execute(f"INSERT INTO {table}_new SELECT * FROM {table}")
                
                # Get row counts
                old_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                new_count = conn.execute(f"SELECT COUNT(*) FROM {table}_new").fetchone()[0]
                
                if old_count != new_count:
                    logger.error(f"Row count mismatch! Old: {old_count}, New: {new_count}")
                    logger.error(f"Aborting migration for {table}")
                    conn.execute(f"DROP TABLE {table}_new")
                    continue
                
                logger.info(f"Verified {new_count} rows copied successfully")
                
                # Swap tables
                conn.execute(f"ALTER TABLE {table} RENAME TO {table}_old")
                conn.execute(f"ALTER TABLE {table}_new RENAME TO {table}")
                
                # Recreate UNIQUE constraint if it was on user_id
                if table == 'user_strategies':
                    try:
                        conn.execute(f"ALTER TABLE {table} ADD CONSTRAINT {table}_user_id_unique UNIQUE (user_id)")
                        logger.info(f"Recreated UNIQUE constraint on {table}.user_id")
                    except Exception as e:
                        logger.warning(f"Could not recreate UNIQUE constraint: {e}")
                
                # Drop old table
                conn.execute(f"DROP TABLE {table}_old")
                logger.info(f"✓ Successfully migrated {table}")
                
            except Exception as e:
                logger.error(f"Error migrating {table}: {e}")
                # Try to cleanup
                try:
                    conn.execute(f"DROP TABLE IF EXISTS {table}_new")
                    conn.execute(f"ALTER TABLE {table}_old RENAME TO {table}")
                except:
                    pass
                logger.error(f"Migration failed for {table}, skipping...")
                continue
        
        conn.close()
        logger.info("✓ Migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Fatal error during migration: {e}")
        return False

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/trading_bot.duckdb"
    success = migrate_database(db_path)
    sys.exit(0 if success else 1)
