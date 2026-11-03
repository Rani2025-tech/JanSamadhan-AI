import sqlite3
from pathlib import Path

db_path = Path("jansamadhan.db")
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check users
    user_cols = [r[1] for r in cur.execute("PRAGMA table_info(users)").fetchall()]
    if "state" not in user_cols:
        cur.execute("ALTER TABLE users ADD COLUMN state VARCHAR(64) DEFAULT 'Odisha'")
        cur.execute("UPDATE users SET state = 'Odisha' WHERE state IS NULL")
        print("Added state column to users table.")

    # Check complaints
    complaint_cols = [r[1] for r in cur.execute("PRAGMA table_info(complaints)").fetchall()]
    if "state" not in complaint_cols:
        cur.execute("ALTER TABLE complaints ADD COLUMN state VARCHAR(64) DEFAULT 'Odisha'")
        cur.execute("UPDATE complaints SET state = 'Odisha' WHERE state IS NULL")
        print("Added state column to complaints table.")

    conn.commit()
    user_count = cur.execute("SELECT count(*) FROM users WHERE state = 'Odisha'").fetchone()[0]
    complaint_count = cur.execute("SELECT count(*) FROM complaints WHERE state = 'Odisha'").fetchone()[0]
    print(f"Migration successful: {user_count} users, {complaint_count} complaints with state='Odisha'.")
    conn.close()

