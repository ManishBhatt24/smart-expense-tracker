from flask import Flask, render_template, session, redirect, url_for
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey123')
app.permanent_session_lifetime = timedelta(days=7)

# Import routes
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.expenses import expenses_bp
from routes.income import income_bp
from routes.analytics import analytics_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(income_bp)
app.register_blueprint(analytics_bp)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))
    return render_template('landing.html')

if __name__ == '__main__':
    app.run(debug=True)
