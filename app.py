from flask import Flask, render_template, request, redirect, flash, session, url_for
from datetime import datetime, timedelta
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from models import init_db

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

init_db()

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    if session.get('role') == 'admin':
        tasks = conn.execute('SELECT * FROM tasks').fetchall()
    else:
        username = session.get('username')
        tasks = conn.execute(
            'SELECT * FROM tasks WHERE assigned_to = ? OR title LIKE ?', 
            (username, f'%{username}%')
        ).fetchall()
    users = conn.execute('SELECT username FROM users').fetchall()
    conn.close()
    return render_template('index.html', tasks=tasks, users=users)

@app.route('/add', methods=['POST'])
def add():
    if 'username' not in session:
        flash('You must be logged in to add a task.')
        return redirect(url_for('login'))

    title = request.form['title']
    assigned_to = request.form['assigned_to']
    due_date_str = request.form['due_date']
    status = request.form['status']

    # Only admin can assign to others
    if session.get('role') == 'user' and assigned_to != session.get('username'):
        flash('You are not allowed to assign tasks to other users.')
        return redirect(request.referrer)

    # --- User existence validation ---
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (assigned_to,)).fetchone()
    if not user:
        conn.close()
        flash('Assigned user does not exist.')
        return redirect(request.referrer)

    # --- Due date validation ---
    today = datetime.today().date()
    if due_date_str:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        if due_date <= today:
            conn.close()
            flash('Due date must be in the future!')
            return redirect(request.referrer)
        elif due_date > today + timedelta(days=365):
            flash('Warning: Due date is more than 12 months ahead!')
    else:
        due_date = today  # Default to today if not provided

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
    if 'username' not in session:
        flash('You must be logged in to edit a task.')
        return redirect(url_for('login'))
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    users = conn.execute('SELECT username FROM users').fetchall()
    conn.close()
    return render_template('edit.html', task=task, users=users)

@app.route('/update/<int:task_id>', methods=['POST'])
def update_task(task_id):
    if 'username' not in session:
        flash('You must be logged in to update a task.')
        return redirect(url_for('login'))
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        hashed_pw = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                (username, hashed_pw, role)
            )
            conn.commit()
            flash('User registered successfully!')
            return redirect('/login')
        except Exception as e:
            flash('Username already exists or error occurred.')
        finally:
            conn.close()
    return render_template('register.html')

# List all users (admin only)
@app.route('/users')
def list_users():
    if session.get('role') != 'admin':
        flash('Only admins can view users.')
        return redirect(url_for('index'))
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, role FROM users').fetchall()
    conn.close()
    return render_template('users.html', users=users)

# Add a new user (admin only)
@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
    if session.get('role') != 'admin':
        flash('Only admins can add users.')
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        hashed_pw = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, hashed_pw, role))
            conn.commit()
            flash('User added successfully!')
            return redirect(url_for('list_users'))
        except Exception:
            flash('Username already exists or error occurred.')
        finally:
            conn.close()
    return render_template('add_user.html')

# Edit a user (admin only)
@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if session.get('role') != 'admin':
        flash('Only admins can edit users.')
        return redirect(url_for('index'))
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        flash('User not found.')
        return redirect(url_for('list_users'))
    if request.method == 'POST':
        username = request.form['username']
        role = request.form['role']
        conn.execute('UPDATE users SET username = ?, role = ? WHERE id = ?', (username, role, user_id))
        conn.commit()
        conn.close()
        flash('User updated successfully!')
        return redirect(url_for('list_users'))
    conn.close()
    return render_template('edit_user.html', user=user)

# Delete a user (admin only)
@app.route('/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if session.get('role') != 'admin':
        flash('Only admins can delete users.')
        return redirect(url_for('index'))
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    flash('User deleted successfully!')
    return redirect(url_for('list_users'))

if __name__ == '__main__':
    app.run(debug=True)
