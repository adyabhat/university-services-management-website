from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import sqlite3
import os
from email.message import EmailMessage

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

def get_db_connection():
    conn = sqlite3.connect('students.db')
    conn.row_factory = sqlite3.Row
    return conn

# Get available rooms dynamically
def get_available_rooms(category):
    all_rooms = [str(i) for i in range(1, 21)]
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT room FROM students")
    room_counts = {}
    for row in c.fetchall():
        room = row[0]
        room_counts[room] = room_counts.get(room, 0) + 1
    conn.close()

    available = []

    for room in all_rooms:
        count = room_counts.get(room, 0)
        if category == 'single':
            if room in [str(i) for i in range(1, 11)] and count == 0:
                available.append(room)
        elif category == 'double':
            if room in [str(i) for i in range(11, 21)] and count < 2:
                available.append(room)
    return available

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/hostel')
def hostel():
    return render_template('hostel-index.html')

@app.route('/hostel/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        department = request.form['department']
        batch = request.form['batch']
        category = request.form['category']
        room = request.form['room']
        

        conn = sqlite3.connect('students.db')
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM students WHERE room = ?", (room,))
        count = c.fetchone()[0]

        if category == 'single' and count >= 1:
            flash(f"❌ Room {room} is already occupied (Single Occupancy).", "danger")
            conn.close()
            return redirect(url_for('register'))

        elif category == 'double' and (int(room) < 11 or count >= 2):
            flash(f"❌ Room {room} is not available for Double Occupancy.", "danger")
            conn.close()
            return redirect(url_for('register'))

        # Insert into DB
        c.execute("""INSERT INTO students (name, age, gender, department, batch, category, room) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (name, age, gender, department, batch, category, room))
        conn.commit()
        conn.close()
        flash(f"✅ Student Registered Successfully!", "success")
        return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/hostel/get-rooms/<category>')
def get_rooms(category):
    available_rooms = get_available_rooms(category)
    return {"rooms": available_rooms}

@app.route('/hostel/students')
def show_students():
    # Get search and filter parameters from the URL
    search_query = request.args.get('search', '')  # Search query for student name
    batch_filter = request.args.get('batch_filter', '')  # Selected batch filter
    department_filter = request.args.get('department_filter', '')  # Selected department filter

    conn = sqlite3.connect('students.db')
    c = conn.cursor()

    # Start building the query to fetch students
    query = "SELECT * FROM students WHERE 1=1"
    params = []

    # Apply search filter by name if search_query exists
    if search_query:
        query += " AND name LIKE ?"
        params.append(f"%{search_query}%")

    # Apply filter by batch if selected
    if batch_filter:
        query += " AND batch = ?"
        params.append(batch_filter)

    # Apply filter by department if selected
    if department_filter:
        query += " AND department = ?"
        params.append(department_filter)

    c.execute(query, params)  # Execute the query with dynamic parameters
    students = c.fetchall()

    # Get distinct batches and departments for dropdowns
    c.execute("SELECT DISTINCT batch FROM students")
    batches = [row[0] for row in c.fetchall()]

    c.execute("SELECT DISTINCT department FROM students")
    departments = [row[0] for row in c.fetchall()]

    conn.close()

    return render_template('students.html', students=students, search_query=search_query, 
                           batch_filter=batch_filter, department_filter=department_filter, 
                           batches=batches, departments=departments)

@app.route('/hostel/delete-student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()
    flash(f"🗑 Student with ID {student_id} has been deleted.", "warning")
    return redirect(url_for('show_students'))

@app.route('/hostel/attendance', methods=['GET', 'POST'])
def attendance():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()

    if request.method == 'POST':
        date = request.form['date']
        student_ids = request.form.getlist('student_ids')

        c.execute("DELETE FROM attendance WHERE date = ?", (date,))

        for sid in student_ids:
            present = f'present_{sid}' in request.form
            c.execute("INSERT INTO attendance (student_id, date, present) VALUES (?, ?, ?)",
                      (sid, date, 1 if present else 0))
        conn.commit()
        conn.close()
        flash(f"✅ Attendance marked for {date}", "success")
        return redirect(url_for('attendance'))

    c.execute("SELECT id, name FROM students")
    students = c.fetchall()
    conn.close()
    today = datetime.today().strftime('%Y-%m-%d')
    return render_template('attendance.html', students=students, today=today)

@app.route('/hostel/menu')
def show_menu():
    conn = get_db_connection()
    menu = conn.execute("SELECT * FROM menu").fetchall()
    conn.close()
    
    structured_menu = {}
    for row in menu:
        day = row['day']
        meal = row['meal']
        if day not in structured_menu:
            structured_menu[day] = {}
        structured_menu[day][meal] = row['items']
    
    # fixed timings
    timings = {
        "breakfast": "7:30 AM - 9:00 AM",
        "lunch": "12:30 PM - 2:00 PM",
        "dinner": "7:00 PM - 8:30 PM"
    }

    return render_template("menu.html", menu=structured_menu, timings=timings)

@app.route('/hostel/update_menu', methods=['POST'])
def update_menu():
    day = request.form['day']
    meal = request.form['meal']
    items = request.form['items']

    conn = get_db_connection()
    conn.execute("UPDATE menu SET items = ? WHERE day = ? AND meal = ?", (items, day, meal))
    conn.commit()
    conn.close()
    return redirect('/hostel/menu')

@app.route('/hostel/attendance-history', methods=['GET', 'POST'])
def attendance_history():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()

    if request.method == 'POST':
        selected_date = request.form['date']
        c.execute('''SELECT s.name, a.present FROM attendance a
                     JOIN students s ON a.student_id = s.id
                     WHERE a.date = ?''', (selected_date,))
        records = c.fetchall()
        conn.close()
        return render_template('attendance_history_result.html', date=selected_date, records=records)
    else:
        conn.close()
        return render_template('attendance_history.html')

@app.route('/housekeeping')
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

@app.route('/housekeeping/feedback', methods=['GET', 'POST'])
def housekeeping_feedback():
    return render_template('housekeeping-feedback.html')

@app.route('/housekeeping/feedback/submit', methods=['POST'])
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
    return redirect("/housekeeping")


def send_feedback_email(user_email, user_feedback):
    msg = EmailMessage()
    msg['Subject'] = 'New Housekeeping Feedback'
    msg['From'] = os.environ.get('HOSTEL_APP_EMAIL')
    msg['To'] = 'recipient_email@example.com'  # Replace with actual recipient email
    msg.set_content(f"Feedback from: {user_email}\n\n{user_feedback}")

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587  # TLS port

    try:
        smtp_password = os.environ.get('HOSTEL_APP_PASSWORD')
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


@app.route('/housekeeping/upgrade', methods=['GET', 'POST'])
def upgrade_page():
    conn = get_db_connection()
    services = [row['service_type'] for row in conn.execute("SELECT DISTINCT service_type FROM housekeeping_companies").fetchall()]
    conn.close()

    # Read optional query parameter from URL
    selected_service = request.args.get('service_type')

    return render_template('housekeeping-upgrade.html', services=services, selected_service=selected_service)

@app.route('/housekeeping/upgrade/submit', methods=['POST'])
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
    
    return redirect('/housekeeping')





import sqlite3
import os

def init_db():
    db_exists = os.path.exists('students.db')
    conn = sqlite3.connect('students.db')
    c = conn.cursor()

    if not db_exists:
        # Create students table
        c.execute('''CREATE TABLE students (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        age INTEGER,
                        gender TEXT,
                        department TEXT,
                        batch TEXT,
                        category TEXT,
                        room TEXT
                    )''')

        # Create attendance table
        c.execute('''CREATE TABLE attendance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER,
                        date TEXT,
                        present INTEGER,
                        FOREIGN KEY(student_id) REFERENCES students(id)
                    )''')

        c.execute('''CREATE TABLE IF NOT EXISTS menu (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        day TEXT NOT NULL,
                        meal TEXT NOT NULL,  -- breakfast/lunch/dinner
                        items TEXT NOT NULL
                    )''')

        print("✅ Database and tables created.")
    else:
        try:
            c.execute('SELECT batch FROM students LIMIT 1')
        except sqlite3.OperationalError:
            c.execute("ALTER TABLE students ADD COLUMN batch TEXT")
            print("✅ Column 'batch' added to students table.")
        
        try:
            c.execute('SELECT department FROM students LIMIT 1')
        except sqlite3.OperationalError:
            c.execute("ALTER TABLE students ADD COLUMN department TEXT")
            print("✅ Column 'department' added to students table.")
        
        try:
            c.execute('SELECT category FROM students LIMIT 1')
        except sqlite3.OperationalError:
            c.execute("ALTER TABLE students ADD COLUMN category TEXT")
            print("✅ Column 'category' added to students table.")
        
        # Ensure attendance table exists (if you added this later)
        try:
            c.execute('SELECT 1 FROM attendance LIMIT 1')
        except sqlite3.OperationalError:
            c.execute('''CREATE TABLE attendance (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            student_id INTEGER,
                            date TEXT,
                            present INTEGER,
                            FOREIGN KEY(student_id) REFERENCES students(id)
                        )''')
            print("✅ Attendance table created.")

        try:
            c.execute("DELETE FROM menu")  # clear old data
        except sqlite3.OperationalError:
            c.execute('''CREATE TABLE IF NOT EXISTS menu (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        day TEXT NOT NULL,
                        meal TEXT NOT NULL,  -- breakfast/lunch/dinner
                        items TEXT NOT NULL
                    )''')

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        meals = ["breakfast", "lunch", "dinner"]

        # fixed options
        breakfast_items = {
            "Monday": "idli-vada, tea, coffee",
            "Tuesday": "dosa, tea, coffee",
            "Wednesday": "poha, tea, coffee",
            "Thursday": "poori, tea, coffee",
            "Friday": "upma, tea, coffee",
            "Saturday": "dosa, tea, coffee",
            "Sunday": "special breakfast, tea, coffee"
        }

        lunch_dinner_items = {
            "default": "rice, sambar, curd, roti-curry, pickle, curd/buttermilk",
            "Sunday": "special lunch/dinner, pickle, curd/buttermilk"
        }

        for day in days:
            c.execute("INSERT INTO menu (day, meal, items) VALUES (?, ?, ?)", (day, "breakfast", breakfast_items[day]))
            
            lunch_items = lunch_dinner_items["Sunday"] if day == "Sunday" else lunch_dinner_items["default"]
            c.execute("INSERT INTO menu (day, meal, items) VALUES (?, ?, ?)", (day, "lunch", lunch_items))
            c.execute("INSERT INTO menu (day, meal, items) VALUES (?, ?, ?)", (day, "dinner", lunch_items))
        
        # Create housekeeping_companies table
        try:
            c.execute('SELECT 1 FROM housekeeping_companies LIMIT 1')
        except sqlite3.OperationalError:
            c.execute('''CREATE TABLE housekeeping_companies (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            company_name TEXT NOT NULL,
                            service_type TEXT NOT NULL,
                            contact_info TEXT NOT NULL,
                            representative_name TEXT NOT NULL
                        )''')
            print("✅ Housekeeping companies table created.")

        # Create housekeeping_companies table
        

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)