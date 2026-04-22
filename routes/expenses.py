from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.db_config import query_db

expenses_bp = Blueprint('expenses', __name__)

@expenses_bp.route('/expenses', methods=['GET'])
def list_expenses():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    expenses = query_db("SELECT * FROM expenses WHERE user_id = %s ORDER BY date DESC", (user_id,))
    return render_template('expenses.html', expenses=expenses)

@expenses_bp.route('/add-expense', methods=['GET', 'POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        user_id = session['user_id']
        amount = request.form['amount']
        category = request.form['category']
        date = request.form['date']
        description = request.form['description']

        query_db("INSERT INTO expenses (user_id, amount, category, date, description) VALUES (%s, %s, %s, %s, %s)", 
                 (user_id, amount, category, date, description))
        flash('Expense added successfully!', 'success')
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('add_expense.html')

@expenses_bp.route('/edit-expense/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        amount = request.form['amount']
        category = request.form['category']
        date = request.form['date']
        description = request.form['description']
        
        query_db("UPDATE expenses SET amount=%s, category=%s, date=%s, description=%s WHERE id=%s AND user_id=%s", 
                 (amount, category, date, description, id, session['user_id']))
        flash('Expense updated!', 'success')
        return redirect(url_for('expenses.list_expenses'))

    expense = query_db("SELECT * FROM expenses WHERE id=%s AND user_id=%s", (id, session['user_id']), one=True)
    return render_template('edit_expense.html', expense=expense)

@expenses_bp.route('/delete-expense/<int:id>')
def delete_expense(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    query_db("DELETE FROM expenses WHERE id=%s AND user_id=%s", (id, session['user_id']))
    flash('Expense deleted!', 'info')
    return redirect(url_for('expenses.list_expenses'))
