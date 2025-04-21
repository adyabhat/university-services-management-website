from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'


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


@app.route('/register', methods=['GET', 'POST'])
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


@app.route('/get-rooms/<category>')
def get_rooms(category):
    available_rooms = get_available_rooms(category)
    return {"rooms": available_rooms}


@app.route('/students', methods=['GET', 'POST'])
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



@app.route('/delete-student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()
    flash(f"🗑 Student with ID {student_id} has been deleted.", "warning")
    return redirect(url_for('show_students'))


@app.route('/attendance', methods=['GET', 'POST'])
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


@app.route('/attendance-history', methods=['GET', 'POST'])
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


def init_db():
    db_exists = os.path.exists('students.db')
    conn = sqlite3.connect('students.db')
    c = conn.cursor()

    if not db_exists:
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

        c.execute('''CREATE TABLE attendance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER,
                        date TEXT,
                        present INTEGER,
                        FOREIGN KEY(student_id) REFERENCES students(id)
                    )''')
        print("✅ Database and tables created.")
    else:
        try:
            c.execute('SELECT category FROM students LIMIT 1')
        except sqlite3.OperationalError:
            c.execute("ALTER TABLE students ADD COLUMN category TEXT")
            print("✅ Column 'category' added to students table.")

    conn.commit()
    conn.close()



if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)