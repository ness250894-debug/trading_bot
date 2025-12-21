-- Add practice_balance column to users table
ALTER TABLE users ADD COLUMN practice_balance DOUBLE DEFAULT 1000.0;
