import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        assigned_to TEXT NOT NULL,
        status TEXT NOT NULL default 'To Do',
        due_date TEXT
    )
''')
conn.commit()
conn.close()