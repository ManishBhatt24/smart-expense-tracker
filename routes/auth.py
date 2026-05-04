from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models.db_config import query_db

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
        
        try:
            # Check if user already exists
            existing_user = query_db("SELECT id FROM users WHERE LOWER(email) = LOWER(%s)", (email,), one=True)
            if existing_user:
                flash('Email already registered!', 'danger')
                return redirect(url_for('auth.register'))

            query_db("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'Registration Error (maybe email exists?): {str(e)}', 'danger')

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = query_db("SELECT * FROM users WHERE LOWER(email) = LOWER(%s)", (email,), one=True)
        
        if user:
            print(f"DEBUG: User found: {email}")
            password_matches = check_password_hash(user['password'], password)
            print(f"DEBUG: Password match: {password_matches}")
            if password_matches:
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                return redirect(url_for('dashboard.dashboard'))
            else:
                flash('Invalid email or password!', 'danger')
        else:
            print(f"DEBUG: User not found: {email}")
            flash('Invalid email or password!', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
