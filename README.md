# Smart Personal Finance & Expense Tracker with Analytics

A full-stack web application built with Flask and MySQL, featuring a modern Glassmorphism UI.

## 🚀 Features
- **Glassmorphism UI**: Modern, transparent, and sleek design.
- **Dashboard**: Visual summaries of income, expenses, and balance.
- **Expense Management**: CRUD operations for daily expenses.
- **Income Management**: Track multiple income sources.
- **Budgeting System**: Set limits and receive warnings.
- **ML Predictions**: Uses Scikit-learn Linear Regression to predict future spending.
- **Data Export**: Export reports in PDF and CSV formats.
- **Dark/Light Mode**: Seamless theme switching.

## 🛠️ Tech Stack
- **Frontend**: HTML5, CSS3, Bootstrap 5, Chart.js
- **Backend**: Python (Flask)
- **Database**: MySQL
- **Data Science**: Pandas, Matplotlib, Scikit-learn

## 📦 Installation & Setup

1. **Clone the project**
   ```bash
   cd smart_finance_tracker
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Setup**
   - Import `database.sql` into your MySQL server.
   - Create a `.env` file based on `.env.example` and update your credentials.

4. **Run the Application**
   ```bash
   python app.py
   ```

## 🗄️ Project Structure
- `templates/`: HTML Jinja2 templates.
- `static/`: CSS, JS, and Images.
- `models/`: Database configuration.
- `routes/`: Flask blueprints for different modules.
- `app.py`: Main application entry point.
