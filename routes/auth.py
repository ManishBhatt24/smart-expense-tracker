from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models.db_config import get_db_connection, close_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
                conn.commit()
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                flash(f'Error: {str(e)}', 'danger')
            finally:
                cursor.close()
                close_connection(conn)
        else:
            flash('Database connection failed!', 'danger')

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            close_connection(conn)

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                return redirect(url_for('dashboard.dashboard'))
            else:
                flash('Invalid email or password!', 'danger')
        else:
            flash('Database connection failed!', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
