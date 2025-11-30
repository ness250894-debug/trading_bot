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
                
                # Step 1: Drop constraints and indexes first
                logger.info(f"Dropping constraints and indexes on {table}...")
                try:
                    # Drop UNIQUE constraint if exists
                    if table == 'user_strategies':
                        conn.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS user_strategies_user_id_key")
                        conn.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS user_strategies_user_id_unique")
                except Exception as e:
                    logger.debug(f"Could not drop constraint (may not exist): {e}")
                
                # Drop all indexes on the table
                try:
                    indexes = conn.execute(f"""
                        SELECT index_name FROM duckdb_indexes() 
                        WHERE table_name = '{table}'
                    """).fetchall()
                    for idx in indexes:
                        try:
                            conn.execute(f"DROP INDEX IF EXISTS {idx[0]}")
                            logger.debug(f"Dropped index {idx[0]}")
                        except:
                            pass
                except Exception as e:
                    logger.debug(f"Could not query/drop indexes: {e}")
                
                # Step 2: Use simpler approach - just alter the column directly
                try:
                    logger.info(f"Altering {table}.user_id to BIGINT...")
                    conn.execute(f"ALTER TABLE {table} ALTER COLUMN user_id TYPE BIGINT")
                    logger.info(f"✓ Successfully migrated {table}.user_id to BIGINT")
                    
                    # Step 3: Recreate constraints
                    if table == 'user_strategies':
                        try:
                            conn.execute(f"ALTER TABLE {table} ADD CONSTRAINT user_strategies_user_id_key UNIQUE (user_id)")
                            logger.info(f"Recreated UNIQUE constraint on {table}.user_id")
                        except Exception as e:
                            logger.warning(f"Could not recreate UNIQUE constraint: {e}")
                    
                except Exception as alter_error:
                    logger.error(f"Direct ALTER failed: {alter_error}")
                    logger.info(f"Trying fallback method with table recreation...")
                    
                    # Fallback: Create new table, copy data, swap
                    try:
                        conn.execute(f"CREATE TABLE {table}_new AS SELECT * FROM {table}")
                        conn.execute(f"ALTER TABLE {table}_new ALTER COLUMN user_id TYPE BIGINT")
                        
                        # Verify counts
                        old_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                        new_count = conn.execute(f"SELECT COUNT(*) FROM {table}_new").fetchone()[0]
                        
                        if old_count != new_count:
                            logger.error(f"Row count mismatch! Old: {old_count}, New: {new_count}")
                            conn.execute(f"DROP TABLE {table}_new")
                            raise Exception("Row count mismatch")
                        
                        logger.info(f"Verified {new_count} rows copied successfully")
                        
                        # Swap
                        conn.execute(f"DROP TABLE {table}")
                        conn.execute(f"ALTER TABLE {table}_new RENAME TO {table}")
                        
                        # Recreate constraint
                        if table == 'user_strategies':
                            try:
                                conn.execute(f"ALTER TABLE {table} ADD CONSTRAINT user_strategies_user_id_key UNIQUE (user_id)")
                                logger.info(f"Recreated UNIQUE constraint")
                            except Exception as e:
                                logger.warning(f"Could not recreate UNIQUE constraint: {e}")
                        
                        logger.info(f"✓ Successfully migrated {table} using fallback method")
                        
                    except Exception as fallback_error:
                        logger.error(f"Fallback method also failed: {fallback_error}")
                        raise
                
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
