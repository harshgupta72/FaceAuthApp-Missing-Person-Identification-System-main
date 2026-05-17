import sqlite3

# Connect to SQLite database (or create if not exists)
conn = sqlite3.connect("database/users.db")
cursor = conn.cursor()

# Create table for users
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    image_path TEXT
)
""")

conn.commit()
conn.close()
print("Database setup completed!")
