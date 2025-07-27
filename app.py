from flask import Flask, render_template, request, redirect, flash
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

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
    due_date_str = request.form['due_date']
    status = request.form['status']

    if due_date_str:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        today = datetime.today().date()
        if due_date <= today:
            flash('Due date must be in the future!')
            return redirect(request.referrer)
        elif due_date > today + timedelta(days=365):
            flash('Warning: Due date is more than 12 months ahead!')

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

@app.route('/update_status/<int:task_id>', methods=['POST'])
def update_status(task_id):
    new_status = request.form['status']
    conn = get_db_connection()
    conn.execute('UPDATE tasks SET status = ? WHERE id = ?', (new_status, task_id))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/edit/<int:task_id>', methods=['GET'])
def edit_task(task_id):
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    conn.close()
    return render_template('edit.html', task=task)

@app.route('/update/<int:task_id>', methods=['POST'])
def update_task(task_id):
    title = request.form['title']
    assigned_to = request.form['assigned_to']
    due_date_str = request.form['due_date']
    status = request.form['status']

    if due_date_str:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        today = datetime.today().date()
        if due_date <= today:
            flash('Due date must be in the future!')
            return redirect(request.referrer)
        elif due_date > today + timedelta(days=365):
            flash('Warning: Due date is more than 12 months ahead!')

    conn = get_db_connection()
    conn.execute('UPDATE tasks SET title = ?, assigned_to = ?, due_date = ?, status = ? WHERE id = ?',
                 (title, assigned_to, due_date, status, task_id))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
