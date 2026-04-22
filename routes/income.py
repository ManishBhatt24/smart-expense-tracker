from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.db_config import query_db

income_bp = Blueprint('income', __name__)

@income_bp.route('/income', methods=['GET', 'POST'])
def add_income():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']

    if request.method == 'POST':
        amount = request.form['amount']
        source = request.form['source']
        from datetime import datetime
        date = datetime.now().strftime('%Y-%m-%d')

        query_db("INSERT INTO income (user_id, amount, source, date) VALUES (%s, %s, %s, %s)", 
                 (user_id, amount, source, date))
        flash('Income added successfully!', 'success')
        return redirect(url_for('dashboard.dashboard'))

    incomes = query_db("SELECT * FROM income WHERE user_id = %s ORDER BY date DESC", (user_id,))
    return render_template('income.html', incomes=incomes)

@income_bp.route('/set-budget', methods=['POST'])
def set_budget():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    amount = request.form['budget_amount']

    # Check if budget exists
    existing = query_db("SELECT id FROM budget WHERE user_id = %s", (user_id,), one=True)

    if existing:
        query_db("UPDATE budget SET limit_amount = %s WHERE user_id = %s", (amount, user_id))
    else:
        query_db("INSERT INTO budget (user_id, limit_amount) VALUES (%s, %s)", (user_id, amount))
    
    flash('Budget updated!', 'success')
    return redirect(url_for('dashboard.dashboard'))
