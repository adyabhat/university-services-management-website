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

# @app.route('/')
# def hostel():
#     return render_template('index.html')


@app.route('/')
@app.route('/menu')
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

@app.route('/update_menu', methods=['POST'])
def update_menu():
    day = request.form['day']
    meal = request.form['meal']
    items = request.form['items']

    conn = get_db_connection()
    conn.execute("UPDATE menu SET items = ? WHERE day = ? AND meal = ?", (items, day, meal))
    conn.commit()
    conn.close()
    return redirect('/menu')


import sqlite3
import os

def init_db():
    db_exists = os.path.exists('students.db')
    conn = sqlite3.connect('students.db')
    c = conn.cursor()

    if not db_exists:
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

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5002, debug=True)