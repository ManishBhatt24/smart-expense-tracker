# Smart Personal Finance & Expense Tracker with Analytics

A full-stack personal finance management system with features for expense tracking, budgeting, and financial insights.

## 🚀 Features
- **Glassmorphism UI**: Modern, transparent, and sleek design.
- **Dashboard**: Visual summaries of income, expenses, and balance.
- **Expense Management**: CRUD operations for daily expenses.
- **Income Management**: Track multiple income sources with edit/delete capabilities.
- **Budgeting System**: Set monthly limits and receive high-visibility warnings.
- **ML Predictions**: Uses Scikit-learn Linear Regression to predict future spending.
- **Data Export**: Export reports in PDF and CSV formats.
- **Dark/Light Mode**: Seamless theme switching with persistence.
- **Database**: Fully migrated to **Supabase (PostgreSQL)** for cloud persistence.

## 🛠️ Tech Stack
- **Frontend**: HTML5, CSS3, Bootstrap 5, Chart.js
- **Backend**: Python (Flask)
- **Database**: Supabase (PostgreSQL)
- **Data Science**: Pandas, Matplotlib, Scikit-learn

## 📦 Installation & Setup

1. **Clone the project**
   ```bash
   git clone https://github.com/ManishBhatt24/smart-expense-tracker
   cd smart_finance_tracker
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Setup**
   - Create a `.env` file based on `.env.example`.
   - Add your `SUPABASE_DB_URL`.
   - The application will automatically initialize the required tables on first run.

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
