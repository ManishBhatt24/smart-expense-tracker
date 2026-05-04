from flask import Blueprint, render_template, session, redirect, url_for, send_file
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from models.db_config import query_db

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
def analytics():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    rows = query_db("SELECT amount, date, category FROM expenses WHERE user_id = %s", (user_id,))
    df = pd.DataFrame(rows)

    category_data = query_db("SELECT category, SUM(amount) as total FROM expenses WHERE user_id = %s GROUP BY category", (user_id,))
    
    monthly_data = query_db("""
        SELECT strftime('%m %Y', date) as month, SUM(amount) as total 
        FROM expenses 
        WHERE user_id = %s AND date >= date('now', '-6 months')
        GROUP BY month 
        ORDER BY MIN(date)
    """, (user_id,))

    prediction = None
    plot_url = None

    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df['month_year'] = df['date'].dt.to_period('M')
        monthly_sums = df.groupby('month_year')['amount'].sum().reset_index()
        monthly_sums['month_index'] = range(len(monthly_sums))

        if len(monthly_sums) >= 2:
            X = monthly_sums[['month_index']]
            y = monthly_sums['amount']
            model = LinearRegression()
            model.fit(X, y)
            prediction = model.predict(np.array([[len(monthly_sums)]]))[0]
        
        plt.figure(figsize=(10, 5))
        plt.plot(monthly_sums['month_year'].astype(str), monthly_sums['amount'], marker='o', color='#6a11cb')
        plt.title('Monthly Spending Trend')
        plt.xlabel('Month')
        plt.ylabel('Amount (₹)')
        plt.grid(True, linestyle='--', alpha=0.7)
        
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', transparent=True)
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode('utf8')
        plt.close()

    return render_template('analytics.html', 
                           prediction=round(prediction, 2) if prediction else "Not enough data", 
                           plot_url=plot_url,
                           category_data=category_data,
                           monthly_data=monthly_data)

@analytics_bp.route('/export/csv')
def export_csv():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    rows = query_db("SELECT amount, category, date, description FROM expenses WHERE user_id = %s", (user_id,))
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Amount', 'Category', 'Date', 'Description'])
    for row in rows:
        cw.writerow([row['amount'], row['category'], row['date'], row['description']])
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='expenses.csv')

@analytics_bp.route('/export/pdf')
def export_pdf():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    rows = query_db("SELECT amount, category, date, description FROM expenses WHERE user_id = %s", (user_id,))
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, f"Expense Report for {session.get('user_name')}")
    y = 700
    p.drawString(100, y, "Amount | Category | Date | Description")
    y -= 20
    for row in rows:
        p.drawString(100, y, f"₹{row['amount']} | {row['category']} | {row['date']} | {row['description'][:30]}")
        y -= 20
        if y < 50:
            p.showPage()
            y = 750
    p.save()
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name='expenses.pdf')
