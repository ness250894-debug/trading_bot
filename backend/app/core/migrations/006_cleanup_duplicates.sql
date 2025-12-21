-- Remove duplicate watchlist entries, keeping the one with the highest ID (latest)
DELETE FROM watchlists 
WHERE id NOT IN (
    SELECT MAX(id) 
    FROM watchlists 
    GROUP BY user_id, symbol
);

-- Add unique index to prevent future duplicates
-- This acts as a constraint: INSERT will fail if (user_id, symbol) exists
CREATE UNIQUE INDEX IF NOT EXISTS idx_watchlist_unique ON watchlists (user_id, symbol);
