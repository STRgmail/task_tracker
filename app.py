from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks').fetchall()
    conn.close()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add():
    title = request.form['title']
    assigned_to = request.form['assigned_to']
    due_date = request.form['due_date']
    status = request.form['status']
    conn = get_db_connection()
    conn.execute('INSERT INTO tasks (title, assigned_to, status, due_date) VALUES (?, ?, ?, ?)',
                 (title, assigned_to, status, due_date))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/filter/<status>')
def filter_tasks(status):
    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks WHERE status = ?", (status,)).fetchall()
    conn.close()
    return render_template('index.html', tasks=tasks)

if __name__ == '__main__':
    app.run(debug=True)
