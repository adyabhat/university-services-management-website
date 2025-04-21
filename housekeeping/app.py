from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
import traceback
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
app.secret_key = 'housekeeping_secret_key'  # Different from main app's secret key

def get_db_connection():
    conn = sqlite3.connect('housekeeping.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def housekeeping_display_companies():
    display_to_service_type = {
        "General Cleaning Services": "Cleaning",
        "Waste Management": "Waste Collection",
        "Washroom & Sanitation": "Sanitation",
        "Outdoor Cleaning": "Outdoor Maintenance",
        "Hardware Assistance": "Maintenance"
    }

    conn = get_db_connection()
    rows = conn.execute("SELECT service_type, company_name FROM housekeeping_companies").fetchall()
    conn.close()

    company_names = {
        display: row['company_name']
        for display, service in display_to_service_type.items()
        for row in rows
        if row['service_type'] == service
    }

    return render_template('housekeeping-index.html', company_names=company_names)

@app.route('/feedback', methods=['GET', 'POST'])
def housekeeping_feedback():
    return render_template('housekeeping-feedback.html')

@app.route('/feedback/submit', methods=['POST'])
def submit_feedback():
    email = request.form['email']
    feedback = request.form['feedback']
    
    # Replace this block with actual email sending logic
    try:
        send_feedback_email(email, feedback)
        flash('Feedback sent successfully! Thank you.', 'success')
    except Exception as e:
        print(f"Failed to send email: {e}")
        flash('Failed to send feedback. Please try again later.', 'danger')
    return redirect("/")

def send_feedback_email(user_email, user_feedback):
    msg = EmailMessage()
    msg['Subject'] = 'New Housekeeping Feedback'
    msg['From'] = os.environ.get('HOUSEKEEPING_APP_EMAIL')
    msg['To'] = 'recipient_email@example.com'  # Replace with actual recipient email
    msg.set_content(f"Feedback from: {user_email}\n\n{user_feedback}")

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587  # TLS port

    try:
        smtp_password = os.environ.get('HOUSEKEEPING_APP_PASSWORD')
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()  # Start TLS encryption
            smtp.login(msg['From'], smtp_password)
            smtp.send_message(msg)
        print("✅ Feedback email sent successfully!")
    except Exception as e:
        # Print the error traceback for detailed information
        print("❌ Failed to send email")
        print("Error Details:")
        traceback.print_exc()  # This will show the detailed error traceback
        raise e  # Raise the error so it can be handled further if needed

@app.route('/thank-you')
def thank_you():
    return "<h1>Thank you for your feedback!</h1><a href='/'>Back to Home</a>"

@app.route('/upgrade', methods=['GET', 'POST'])
def upgrade_page():
    conn = get_db_connection()
    services = [row['service_type'] for row in conn.execute("SELECT DISTINCT service_type FROM housekeeping_companies").fetchall()]
    conn.close()

    # Read optional query parameter from URL
    selected_service = request.args.get('service_type')

    return render_template('housekeeping-upgrade.html', services=services, selected_service=selected_service)

@app.route('/upgrade/submit', methods=['POST'])
def submit_upgrade():
    service_type = request.form['service']
    company_name = request.form['company_name']
    contact_info = request.form['contact_info']
    rep_name = request.form['rep_name']

    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM housekeeping_companies WHERE service_type = ?", (service_type,)).fetchone()

    if existing:
        # Update existing entry
        conn.execute("""
            UPDATE housekeeping_companies 
            SET company_name = ?, contact_info = ?, representative_name = ?
            WHERE service_type = ?
        """, (company_name, contact_info, rep_name, service_type))
        flash(f"✅ {company_name} upgraded for {service_type}.", "success")
    else:
        # Insert new entry
        conn.execute("""
            INSERT INTO housekeeping_companies (company_name, contact_info, representative_name, service_type)
            VALUES (?, ?, ?, ?)
        """, (company_name, contact_info, rep_name, service_type))
        flash(f"✅ {company_name} registered for {service_type}.", "success")

    conn.commit()
    conn.close()
    
    return redirect('/')

def init_db():
    db_exists = os.path.exists('housekeeping.db')
    conn = sqlite3.connect('housekeeping.db')
    c = conn.cursor()

    if not db_exists:
        # Create housekeeping_companies table
        c.execute('''CREATE TABLE housekeeping_companies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_name TEXT NOT NULL,
                        service_type TEXT NOT NULL,
                        contact_info TEXT NOT NULL,
                        representative_name TEXT NOT NULL
                    )''')
        print("✅ Housekeeping database and tables created.")

        # Insert some default data for testing
        default_companies = [
            ("CleanPro Services", "Cleaning", "contact@cleanpro.com", "John Smith"),
            ("Waste Warriors", "Waste Collection", "info@wastewarriors.com", "Sarah Johnson"),
            ("SaniTech", "Sanitation", "support@sanitech.com", "Michael Brown"),
            ("OutdoorPlus", "Outdoor Maintenance", "service@outdoorplus.com", "Jessica Davis"),
            ("FixIt Solutions", "Maintenance", "help@fixitsolutions.com", "Robert Wilson")
        ]
        
        c.executemany("""
            INSERT INTO housekeeping_companies (company_name, service_type, contact_info, representative_name)
            VALUES (?, ?, ?, ?)
        """, default_companies)
        
        print("✅ Default housekeeping companies inserted.")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5003, debug=True)