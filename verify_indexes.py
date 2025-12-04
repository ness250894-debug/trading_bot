import duckdb

conn = duckdb.connect('backend/data/trading_bot.duckdb')
indexes = conn.execute("SELECT * FROM pg_indexes WHERE tablename = 'bot_configurations'").fetchall()
print("Indexes on bot_configurations:")
for idx in indexes:
    print(idx)

conn.close()
