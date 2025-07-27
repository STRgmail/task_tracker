import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'user'))
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            assigned_to TEXT NOT NULL,
            status TEXT NOT NULL,
            due_date DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assigned_to) REFERENCES users(username)
        )
    ''')
    # Optional: trigger to auto-update updated_at
    conn.execute('''
        CREATE TRIGGER IF NOT EXISTS update_task_updated_at
        AFTER UPDATE ON tasks
        FOR EACH ROW
        BEGIN
            UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
    ''')
    conn.commit()
    conn.close()