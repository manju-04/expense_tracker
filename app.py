import streamlit as st
import sqlite3
from datetime import datetime
import csv
from fpdf import FPDF
import matplotlib.pyplot as plt
import re
import pandas as pd
import tempfile
import os

# Database connection setup
def connect_to_db():
    return sqlite3.connect('expense_tracker.db')

# User table creation
def initialize_db():
    db = connect_to_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            userid INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(255),
            email VARCHAR(255),
            password VARCHAR(255)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            expid INTEGER PRIMARY KEY AUTOINCREMENT,
            userid INTEGER,
            category VARCHAR(255),
            description TEXT,
            amount REAL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (userid) REFERENCES users(userid)
        )
    """)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS income (
            income_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            income_amount DECIMAL(10, 2),
            FOREIGN KEY (user_id) REFERENCES users(userid)
        )
    ''')
    db.commit()
    db.close()

initialize_db()

# Helper functions
def validate_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def validate_password(password):
    return len(password) > 0

def get_balance(user_id):
    db = connect_to_db()
    cursor = db.cursor()
    
    # Get total income for the user
    cursor.execute("SELECT SUM(income_amount) FROM income WHERE user_id=?", (user_id,))
    total_income = cursor.fetchone()[0] or 0  # If no income, set to 0
    
    # Get total expenses for the user
    cursor.execute("SELECT SUM(amount) FROM expenses WHERE userid=?", (user_id,))
    total_expenses = cursor.fetchone()[0] or 0  # If no expenses, set to 0
    
    # Ensure both values are float for subtraction
    total_income = float(total_income)
    total_expenses = float(total_expenses)
    
    db.close()
    
    # Calculate balance
    balance = total_income - total_expenses
    return balance

def generate_pdf(rows, user_id):
    filename = "expenses.pdf"
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, txt="Personal Expense Tracker", ln=True, align='C')
    pdf.ln(10)

    db = connect_to_db()
    cursor = db.cursor()

    # Get highest spending category
    cursor.execute("""
        SELECT category, SUM(amount) as total_spent
        FROM expenses 
        WHERE userid = ?
        GROUP BY category
        ORDER BY total_spent DESC
        LIMIT 1
    """, (user_id,))
    
    result = cursor.fetchone()
    
    if result:
        category, total_spent = result
        
        # Display the Highest Spending Category Information
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Highest Spending Category: {category}", ln=True, align='L')
        pdf.cell(200, 10, txt=f"Total Spent: {total_spent}", ln=True, align='L')
        pdf.ln(10)
    
    # Table Header (Bold)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(40, 10, 'Category', border=1, align='C')
    pdf.cell(70, 10, 'Description', border=1, align='C')
    pdf.cell(30, 10, 'Amount', border=1, align='C')
    pdf.cell(40, 10, 'Date', border=1, align='C')
    pdf.ln()

    # Table Rows
    pdf.set_font("Arial", size=12)
    for row in rows:
        pdf.cell(40, 10, row[0], border=1, align='C')
        pdf.cell(70, 10, row[1], border=1, align='C')
        pdf.cell(30, 10, str(row[2]), border=1, align='C')
        pdf.cell(40, 10, str(row[3]), border=1, align='C')
        pdf.ln()

    pdf.output(filename)
    return filename

# Streamlit App
def main():
    st.set_page_config(
        page_title="Personal Expense Tracker",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if 'userid' not in st.session_state:
        st.session_state.userid = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'categories' not in st.session_state:
        st.session_state.categories = ["Food", "Transport", "Shopping", "Utilities", "Entertainment", "Health"]
    if 'page' not in st.session_state:
        st.session_state.page = "home"
    
    # Navigation
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "register":
        register_page()
    elif st.session_state.page == "forgot_password":
        forgot_password_page()
    elif st.session_state.page == "income":
        income_page()
    elif st.session_state.page == "menu":
        menu_page()
    elif st.session_state.page == "add_expense":
        add_expense_page()
    elif st.session_state.page == "delete_expense":
        delete_expense_page()
    elif st.session_state.page == "update_expense":
        update_expense_page()
    elif st.session_state.page == "view_expense":
        view_expense_page()

def home_page():
    st.title("Welcome to Your Personal Expense Tracker")
    st.markdown("<h2 style='text-align: center;'>Track, Save, Succeed!</h2>", unsafe_allow_html=True)
    
    st.write("")
    st.write("💰 Take control of your finances today!")
    st.write("📊 Track every rupee, save every penny.")
    st.write("🌟 Your journey to smart spending starts here!")
    
    st.write("")
    st.write("Already have an account?")
    if st.button("Login", key="home_login"):
        st.session_state.page = "login"
        st.rerun()
    
    st.write("Are you a new user?")
    if st.button("Register", key="home_register"):
        st.session_state.page = "register"
        st.rerun()

def login_page():
    st.title("Login")
    
    with st.form("login_form"):
        email = st.text_input("Enter your Email:")
        password = st.text_input("Enter your Password:", type="password")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            login_submit = st.form_submit_button("Login")
        with col2:
            if st.form_submit_button("Forgot Password?"):
                st.session_state.page = "forgot_password"
                st.rerun()
        with col3:
            if st.form_submit_button("Back"):
                st.session_state.page = "home"
                st.rerun()
    
    if login_submit:
        if not validate_email(email):
            st.error("Invalid email format")
            return
        
        if not validate_password(password):
            st.error("Password is required")
            return
            
        db = connect_to_db()
        cursor = db.cursor()
        cursor.execute("SELECT userid, username FROM users WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()
        db.close()

        if user:
            st.session_state.userid, st.session_state.username = user
            st.success("Login Successful")
            
            # Check if income already exists for the user
            db = connect_to_db()
            cursor = db.cursor()
            cursor.execute("SELECT income_amount FROM income WHERE user_id=?", (st.session_state.userid,))
            income = cursor.fetchone()
            db.close()

            if income:
                st.session_state.page = "menu"
            else:
                st.session_state.page = "income"
            st.rerun()
        else:
            st.error("Invalid email or password")

def forgot_password_page():
    st.title("Forgot Password")
    
    email = st.text_input("Enter your registered email")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Reset Password"):
            if not email:
                st.error("Email is required")
                return
                
            db = connect_to_db()
            cursor = db.cursor()
            cursor.execute("SELECT userid FROM users WHERE email=?", (email,))
            user = cursor.fetchone()
            db.close()

            if user:
                st.session_state.temp_email = email
                st.session_state.page = "reset_password"
                st.rerun()
            else:
                st.error("Email not found")
    
    with col2:
        if st.button("Back"):
            st.session_state.page = "login"
            st.rerun()
    
    if 'temp_email' in st.session_state:
        new_password = st.text_input("Enter new password:", type="password")
        confirm_password = st.text_input("Confirm new password:", type="password")
        
        if st.button("Submit New Password"):
            if new_password and new_password == confirm_password:
                db = connect_to_db()
                cursor = db.cursor()
                cursor.execute("UPDATE users SET password=? WHERE email=?", (new_password, st.session_state.temp_email))
                db.commit()
                db.close()
                st.success("Password reset successfully")
                del st.session_state.temp_email
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error("Passwords don't match")

def register_page():
    st.title("Register")
    
    with st.form("register_form"):
        username = st.text_input("Enter your Username:")
        email = st.text_input("Enter your Email:")
        password = st.text_input("Enter your Password:", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            register_submit = st.form_submit_button("Register")
        with col2:
            if st.form_submit_button("Back"):
                st.session_state.page = "home"
                st.rerun()
    
    if register_submit:
        if not validate_email(email):
            st.error("Invalid email format")
            return

        if not validate_password(password):
            st.error("Password is required")
            return
            
        db = connect_to_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                       (username, email, password))
        db.commit()
        db.close()

        st.success("Registration Successful")
        st.session_state.page = "login"
        st.rerun()

def income_page():
    st.title("Track Your Earnings, Shape Your Future!")
    st.markdown("> *Income is the key to financial freedom. Let's start with a step!*")
    
    income_amount = st.number_input("Enter your monthly income:", min_value=0.0, step=0.01)
    
    if st.button("Submit"):
        if not income_amount:
            st.error("Please enter your income")
            return

        try:
            conn = connect_to_db()
            cursor = conn.cursor()
            query = "INSERT INTO income (user_id, income_amount) VALUES (?, ?)"
            cursor.execute(query, (st.session_state.userid, income_amount))
            conn.commit()
            conn.close()
            st.success("Income recorded successfully!")
            st.session_state.page = "menu"
            st.rerun()
        except Exception as err:
            st.error(f"Error: {err}")

def menu_page():
    balance = get_balance(st.session_state.userid)
    balance_status = f"Balance: ₹{balance:.2f}"
    if balance < 0:
        balance_status = f"Over Budget: ₹{abs(balance):.2f}"
    
    st.title(f"{st.session_state.username}'s Personal Expense Tracker")
    st.header("Menu")
    
    if balance >= 0:
        st.success(balance_status)
    else:
        st.error(balance_status)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add Expense", use_container_width=True):
            st.session_state.page = "add_expense"
            st.rerun()
        
        if st.button("Delete Expense", use_container_width=True):
            st.session_state.page = "delete_expense"
            st.rerun()
        
        if st.button("Update Expense", use_container_width=True):
            st.session_state.page = "update_expense"
            st.rerun()
    
    with col2:
        if st.button("View Expense", use_container_width=True):
            st.session_state.page = "view_expense"
            st.rerun()
        
        if st.button("Update Income", use_container_width=True):
            update_income()
        
        if st.button("Logout", use_container_width=True):
            st.session_state.userid = None
            st.session_state.username = None
            st.session_state.page = "home"
            st.rerun()

def update_income():
    new_income = st.number_input("Enter your new income:", min_value=0.0, step=0.01, key="update_income")
    
    if st.button("Update Income"):
        try:
            conn = connect_to_db()  
            cursor = conn.cursor()
            cursor.execute("UPDATE income SET income_amount = ? WHERE user_id = ?", 
                          (new_income, st.session_state.userid))
            conn.commit()
            conn.close()
            st.success("Income updated successfully!")
            st.rerun()
        except Exception as err:
            st.error(f"Error: {err}")

def add_expense_page():
    st.title("Add Expense")
    st.markdown("> *Shape Your Financial Journey!*")
    
    category = st.selectbox("Select your Category:", st.session_state.categories)
    
    if st.button("Add New Category"):
        new_category = st.text_input("Enter new category:")
        if new_category and new_category not in st.session_state.categories:
            st.session_state.categories.append(new_category)
            st.success("New category added.")
    
    description = st.text_input("Enter Description:")
    amount = st.number_input("Enter Amount:", min_value=0.0, step=0.01)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save"):
            if not category or not description or not amount:
                st.error("All fields are required")
                return

            db = connect_to_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO expenses (userid, category, description, amount) VALUES (?, ?, ?, ?)",
                           (st.session_state.userid, category, description, float(amount)))
            db.commit()
            db.close()

            st.success("Expense Added Successfully")
            st.session_state.page = "menu"
            st.rerun()
    
    with col2:
        if st.button("Back"):
            st.session_state.page = "menu"
            st.rerun()

def delete_expense_page():
    st.title("Delete Expense")
    st.markdown("> *Remove unwanted expenses and keep your budget in check!*")
    
    category = st.selectbox("Select Category:", st.session_state.categories)
    description = st.text_input("Enter Description:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Delete"):
            if not category or not description:
                st.error("All fields are required")
                return

            db = connect_to_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM expenses WHERE userid=? AND category=? AND description=?", 
                           (st.session_state.userid, category, description))
            db.commit()
            db.close()

            st.success("Expense Deleted Successfully")
            st.session_state.page = "menu"
            st.rerun()
    
    with col2:
        if st.button("Back"):
            st.session_state.page = "menu"
            st.rerun()

def update_expense_page():
    st.title("Update Expense")
    st.markdown("> *Edit and keep track of your expenses for better budgeting!*")
    
    category = st.selectbox("Select Category:", st.session_state.categories)
    old_description = st.text_input("Enter Old Description:")
    new_description = st.text_input("Enter New Description:")
    new_amount = st.number_input("Enter New Amount:", min_value=0.0, step=0.01)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Update"):
            if not category or not old_description or not new_description or not new_amount:
                st.error("All fields are required")
                return

            db = connect_to_db()
            cursor = db.cursor()
            cursor.execute("""
                UPDATE expenses SET description=?, amount=? WHERE userid=? AND category=? AND description=?
            """, (new_description, float(new_amount), st.session_state.userid, category, old_description))
            db.commit()
            db.close()

            st.success("Expense Updated Successfully")
            st.session_state.page = "menu"
            st.rerun()
    
    with col2:
        if st.button("Back"):
            st.session_state.page = "menu"
            st.rerun()

def view_expense_page():
    st.title("VIEW EXPENSE")
    st.markdown("> *Track your expenses and get insights into your spending patterns!*")
    
    st.header("Table View")
    category = st.selectbox("View by Category", ["All"] + st.session_state.categories)
    
    if st.button("View"):
        db = connect_to_db()
        cursor = db.cursor()
        query = "SELECT category, description, amount, date FROM expenses WHERE userid=?"
        params = [st.session_state.userid]

        if category != "All":
            query += " AND category=?"
            params.append(category)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        db.close()
        
        if rows:
            df = pd.DataFrame(rows, columns=["Category", "Description", "Amount", "Date"])
            st.dataframe(df)
            
            # Export options
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Export to CSV"):
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"expenses_{st.session_state.userid}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                if st.button("Export to PDF"):
                    pdf_file = generate_pdf(rows, st.session_state.userid)
                    with open(pdf_file, "rb") as file:
                        st.download_button(
                            label="Download PDF",
                            data=file,
                            file_name="expenses.pdf",
                            mime="application/pdf"
                        )
        else:
            st.info("No expenses found for the selected category.")
    
    st.header("Graphical Representation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Bar Chart"):
            db = connect_to_db()
            cursor = db.cursor()
            cursor.execute("SELECT category, SUM(amount) FROM expenses WHERE userid=? GROUP BY category", (st.session_state.userid,))
            data = cursor.fetchall()
            db.close()

            if data:
                categories = [row[0] for row in data]
                amounts = [row[1] for row in data]

                fig, ax = plt.subplots()
                ax.bar(categories, amounts, color=["blue", "orange", "green", "red", "purple", "brown"])
                ax.set_title("Expense Categories")
                ax.set_xlabel("Category")
                ax.set_ylabel("Amount")
                for i in range(len(categories)):
                    ax.text(i, amounts[i] + 1, str(amounts[i]), ha='center')
                st.pyplot(fig)
            else:
                st.info("No data available for chart.")
    
    with col2:
        if st.button("Pie Chart"):
            db = connect_to_db()
            cursor = db.cursor()
            cursor.execute("SELECT category, SUM(amount) FROM expenses WHERE userid=? GROUP BY category", (st.session_state.userid,))
            data = cursor.fetchall()
            db.close()

            if data:
                categories = [row[0] for row in data]
                amounts = [row[1] for row in data]

                fig, ax = plt.subplots()
                ax.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90)
                ax.set_title("Expense Distribution by Category")
                st.pyplot(fig)
            else:
                st.info("No data available for chart.")
    
    if st.button("Back to Menu"):
        st.session_state.page = "menu"
        st.rerun()

if __name__ == "__main__":
    main()
