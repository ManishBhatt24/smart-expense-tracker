from flask import Blueprint, render_template, session, redirect, url_for
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    from models.db_config import query_db
    
    def safe_float(val):
        try:
            if val is None or str(val).strip() == "":
                return 0.0
            return float(val)
        except:
            return 0.0

    # Get total income
    total_income_row = query_db("SELECT SUM(amount) as total FROM income WHERE user_id = %s", (user_id,), one=True)
    total_income = safe_float(total_income_row['total'])
    
    # Get total expenses
    total_expenses_row = query_db("SELECT SUM(amount) as total FROM expenses WHERE user_id = %s", (user_id,), one=True)
    total_expenses = safe_float(total_expenses_row['total'])
    
    balance = total_income - total_expenses
    
    # Get recent transactions (expenses)
    recent_expenses = query_db("SELECT * FROM expenses WHERE user_id = %s ORDER BY id DESC LIMIT 5", (user_id,))

    # Get category-wise expenses for pie chart
    category_data = query_db("SELECT category, SUM(amount) as total FROM expenses WHERE user_id = %s GROUP BY category", (user_id,))
    
    # Get monthly expenses for bar chart (last 6 months)
    monthly_data = query_db("""
        SELECT strftime('%m %Y', date) as month, SUM(amount) as total 
        FROM expenses 
        WHERE user_id = %s AND date >= date('now', '-6 months')
        GROUP BY month 
        ORDER BY MIN(date)
    """, (user_id,))

    # Get budget info
    budget_row = query_db("SELECT limit_amount FROM budget WHERE user_id = %s", (user_id,), one=True)
    budget_limit = safe_float(budget_row['limit_amount'] if budget_row else 0)
    
    # Budget alert check
    month_total_row = query_db("SELECT SUM(amount) as month_total FROM expenses WHERE user_id = %s AND strftime('%m', date) = strftime('%m', 'now')", (user_id,), one=True)
    current_month_total = safe_float(month_total_row['month_total'])
    
    budget_status = None
    if budget_limit > 0:
        percent = (current_month_total / budget_limit) * 100
        if percent >= 100:
            budget_status = 'exceeded'
        elif percent >= 80:
            budget_status = 'warning'

    return render_template('dashboard.html', 
                           total_income=total_income, 
                           total_expenses=total_expenses, 
                           balance=balance,
                           recent_expenses=recent_expenses,
                           category_data=category_data,
                           monthly_data=monthly_data,
                           budget_limit=budget_limit,
                           budget_status=budget_status)
