from flask import Flask, render_template, request, flash
from pymongo import MongoClient
import json
import re
import random
from datetime import timedelta, datetime


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# MongoDB connection
client = MongoClient("mongodb+srv://abhishekbhat11:BHAyankara11@cluster0.puhein0.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["schedule_db"]
collection = db["schedules"]

def parse_schedule_response(response_text):
    try:
        # Find JSON-like string from LLM output
        json_data = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_data:
            parsed = json.loads(json_data.group())
            return parsed
        else:
            return None
    except Exception as e:
        print("Parsing failed:", e)
        return None

def validate_schedule_possibility(subjects, classes_per_day, day_start_time, day_end_time, duration, short_break_time, lunch_break_time):
    """Check if the requested schedule is feasible within the time constraints"""
    start_time = datetime.strptime(day_start_time, "%H:%M")
    end_time = datetime.strptime(day_end_time, "%H:%M")
    
    # Calculate total available minutes in a day
    total_day_minutes = (end_time - start_time).total_seconds() / 60
    
    # Short break (15 minutes)
    short_break_minutes = 15
    
    # Lunch break (30 minutes)
    lunch_break_minutes = 30
    
    # Calculate total time needed for classes and breaks
    total_needed_minutes = (classes_per_day * duration) + short_break_minutes + lunch_break_minutes
    
    # Check if there's enough time in the day
    return total_needed_minutes <= total_day_minutes, total_needed_minutes, total_day_minutes

def get_time_of_day(time_str):
    """Determine if a time is morning, midday or afternoon"""
    hour = int(time_str.split(":")[0])
    if hour < 12:
        return "morning"
    elif hour < 15:
        return "midday"
    else:
        return "afternoon"

def generate_schedule(subjects, classes_per_day, days_per_week, preferred_times=None):
    """Generate a schedule that ensures preferred times are allocated"""
    # Get subject names and classes per week
    subject_names = [s["name"] for s in subjects]
    classes_per_week = {s["name"]: s["classes_per_week"] for s in subjects}
    
    # Calculate total classes needed
    total_classes_needed = sum(classes_per_week.values())
    total_class_slots = classes_per_day * days_per_week
    
    # Check if we have enough slots
    if total_classes_needed > total_class_slots:
        return None
    
    # Initialize the schedule with empty lists for each day
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    schedule = {day: [None] * classes_per_day for day in days[:days_per_week]}
    
    # Keep track of remaining classes per subject
    remaining_classes = classes_per_week.copy()
    
    # First pass: Allocate preferred time slots (COMPULSORY)
    if preferred_times:
        for subject_name, preferences in preferred_times.items():
            for day, slot_indices in preferences.items():
                for slot_index in slot_indices:
                    if slot_index < classes_per_day and day in schedule:
                        # Check if the slot is already allocated
                        if schedule[day][slot_index] is not None:
                            flash(f"Conflict detected: Multiple subjects preferred for the same slot on {day}", "error")
                            return None
                        
                        # Allocate this preferred slot
                        schedule[day][slot_index] = subject_name
                        remaining_classes[subject_name] -= 1
                        
                        # If we've allocated all needed classes for this subject, break
                        if remaining_classes[subject_name] <= 0:
                            break
    
    # Second pass: Fill remaining slots
    for day in schedule.keys():
        for slot_index in range(classes_per_day):
            # Skip already allocated slots
            if schedule[day][slot_index] is not None:
                continue
                
            # Find subjects that still need classes
            available_subjects = [s for s, r in remaining_classes.items() if r > 0]
            
            if available_subjects:
                # Determine time of day for this period
                time_of_day = get_time_of_day_for_period(slot_index, classes_per_day)
                
                # Sort subjects randomly (without feedback system)
                random.shuffle(available_subjects)
                
                # Take the first subject
                subject = available_subjects[0]
                schedule[day][slot_index] = subject
                remaining_classes[subject] -= 1
            else:
                schedule[day][slot_index] = "Free"
    
    # Third pass: Check for consecutive same subjects and redistribute if needed
    for day in schedule.keys():
        for i in range(len(schedule[day]) - 1):
            if schedule[day][i] == schedule[day][i + 1] and schedule[day][i] != "Free":
                # Find a different day to swap with
                for other_day in schedule.keys():
                    if other_day != day:
                        for j in range(len(schedule[other_day])):
                            # Don't swap preferred time slots
                            if is_preferred_slot(other_day, j, preferred_times) or is_preferred_slot(day, i+1, preferred_times):
                                continue
                                
                            # Ensure we're not creating a new consecutive pair
                            if (schedule[other_day][j] != schedule[day][i] and 
                                (j == 0 or schedule[other_day][j-1] != schedule[day][i+1]) and 
                                (j == len(schedule[other_day])-1 or schedule[other_day][j+1] != schedule[day][i+1])):
                                # Swap subjects
                                schedule[day][i+1], schedule[other_day][j] = schedule[other_day][j], schedule[day][i+1]
                                break
                    # If we found a swap, break out of the outer loop too
                    if schedule[day][i] != schedule[day][i + 1]:
                        break
    
    return schedule

def get_time_of_day_for_period(period_index, total_periods):
    """Map a period index to morning, midday, or afternoon"""
    relative_position = period_index / total_periods
    
    if relative_position < 0.33:
        return "morning"
    elif relative_position < 0.67:
        return "midday"
    else:
        return "afternoon"

def is_preferred_slot(day, slot_index, preferred_times):
    """Check if a slot is in the preferred times for any subject"""
    if preferred_times:
        for subject, preferences in preferred_times.items():
            if day in preferences and slot_index in preferences[day]:
                return True
    return False

def optimize_break_placement(schedule, short_break_time, lunch_break_time, duration):
    """Optimize when breaks occur based on the schedule"""
    start_time = datetime.strptime(short_break_time, "%H:%M")
    lunch_time = datetime.strptime(lunch_break_time, "%H:%M")
    
    # Short break should ideally be after 1/3 of the day
    # Lunch break should ideally be in the middle of the day
    
    # Calculate ideal positions
    days = list(schedule.keys())
    
    for day in days:
        subjects = schedule[day]
        num_periods = len(subjects)
        
        # Ideal positions (as period indices)
        ideal_short_break = int(num_periods * 0.33)
        ideal_lunch_break = int(num_periods * 0.5)
        
        # If the breaks would be adjacent, separate them more
        if abs(ideal_short_break - ideal_lunch_break) <= 1:
            ideal_short_break = max(1, int(num_periods * 0.25))
            ideal_lunch_break = min(num_periods - 2, int(num_periods * 0.6))
        
        # Update break times based on ideal positions
        short_break_hour = start_time.hour + (ideal_short_break * duration // 60)
        short_break_minute = start_time.minute + (ideal_short_break * duration % 60)
        
        # Handle minute overflow
        if short_break_minute >= 60:
            short_break_hour += 1
            short_break_minute -= 60
        
        lunch_hour = start_time.hour + (ideal_lunch_break * duration // 60)
        lunch_minute = start_time.minute + (ideal_lunch_break * duration % 60)
        
        # Handle minute overflow
        if lunch_minute >= 60:
            lunch_hour += 1
            lunch_minute -= 60
        
        # Format the new times
        optimized_short_break = f"{short_break_hour:02d}:{short_break_minute:02d}"
        optimized_lunch_break = f"{lunch_hour:02d}:{lunch_minute:02d}"
        
        # Return the first day's optimized times (could be different for each day)
        return optimized_short_break, optimized_lunch_break

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        total_subjects = int(request.form["total_subjects"])
        duration = int(request.form["duration"])
        classes_per_day = int(request.form["classes_per_day"])
        days_per_week = int(request.form["days_per_week"])
        
        # Get start and end times of the day
        day_start_time = request.form["day_start_time"]
        day_end_time = request.form["day_end_time"]
        
        # Get break times
        short_break_time = request.form["short_break_time"]
        lunch_break_time = request.form["lunch_break_time"]
        
        # Get subject preferences if provided
        subject_preferences = {}
        for i in range(total_subjects):
            name = request.form[f"subject_name_{i}"]
            per_week = int(request.form[f"subject_weekly_{i}"])
            
            # Check if preference times were provided
            preferred_times = {}
            for key in request.form:
                # Format: pref_time_{subject_index}_{day}_{period}
                if key.startswith(f"pref_time_{i}_"):
                    parts = key.split('_')
                    if len(parts) >= 5:
                        day = parts[3]
                        period = int(parts[4])
                        
                        if day not in preferred_times:
                            preferred_times[day] = []
                        
                        preferred_times[day].append(period)
            
            # Add subject info and preferences
            subject_info = {
                "name": name,
                "classes_per_week": per_week
            }
            
            if preferred_times:
                subject_preferences[name] = preferred_times
        
        subjects = []
        for i in range(total_subjects):
            name = request.form[f"subject_name_{i}"]
            per_week = int(request.form[f"subject_weekly_{i}"])
            subjects.append({"name": name, "classes_per_week": per_week})
        
        # Check if schedule is possible within time constraints
        is_possible, needed_minutes, available_minutes = validate_schedule_possibility(
            subjects, classes_per_day, day_start_time, day_end_time, 
            duration, short_break_time, lunch_break_time
        )
        
        if not is_possible:
            flash(f"Schedule not possible within the specified time constraints. You need {needed_minutes} minutes but only have {available_minutes} minutes available.", "error")
            return render_template("index.html")
        
        # Optimize break placement (if auto-optimize is enabled)
        if "optimize_breaks" in request.form and request.form["optimize_breaks"] == "yes":
            # Generate a temporary schedule to optimize breaks
            temp_schedule = generate_schedule(subjects, classes_per_day, days_per_week)
            if temp_schedule:
                short_break_time, lunch_break_time = optimize_break_placement(
                    temp_schedule, short_break_time, lunch_break_time, duration
                )
        
        # Generate the schedule (with mandatory preferred times)
        parsed_schedule = generate_schedule(
            subjects, classes_per_day, days_per_week, 
            preferred_times=subject_preferences
        )
        
        if not parsed_schedule:
            flash("Failed to generate a valid schedule. There are more total classes required than available slots or there's a conflict in preferred time slots.", "error")
            return render_template("index.html")

        # Create time slots based on start and end times
        start_time = datetime.strptime(day_start_time, "%H:%M")
        end_time = datetime.strptime(day_end_time, "%H:%M")
        short_break_start = datetime.strptime(short_break_time, "%H:%M")
        lunch_break_start = datetime.strptime(lunch_break_time, "%H:%M")
        
        # Create a list of all time slots for the day
        time_slots = []
        current_time = start_time
        
        while current_time < end_time:
            slot_end = current_time + timedelta(minutes=duration)
            
            # Don't create slots that go beyond the end time
            if slot_end > end_time:
                slot_end = end_time
            
            # Check for short break
            if (current_time <= short_break_start < slot_end):
                # Add time slot until break
                if current_time < short_break_start:
                    time_slots.append({
                        "start": current_time,
                        "end": short_break_start,
                        "label": f"{current_time.strftime('%I:%M %p')} - {short_break_start.strftime('%I:%M %p')}",
                        "is_break": False
                    })
                
                # Add short break
                break_end = short_break_start + timedelta(minutes=15)
                # Ensure break doesn't go beyond end time
                if break_end > end_time:
                    break_end = end_time
                
                time_slots.append({
                    "start": short_break_start,
                    "end": break_end,
                    "label": f"{short_break_start.strftime('%I:%M %p')} - {break_end.strftime('%I:%M %p')}",
                    "is_break": True,
                    "break_type": "Short Break"
                })
                
                current_time = break_end
                continue
                
            # Check for lunch break
            if (current_time <= lunch_break_start < slot_end):
                # Add time slot until break
                if current_time < lunch_break_start:
                    time_slots.append({
                        "start": current_time,
                        "end": lunch_break_start,
                        "label": f"{current_time.strftime('%I:%M %p')} - {lunch_break_start.strftime('%I:%M %p')}",
                        "is_break": False
                    })
                
                # Add lunch break
                break_end = lunch_break_start + timedelta(minutes=30)
                # Ensure break doesn't go beyond end time
                if break_end > end_time:
                    break_end = end_time
                
                time_slots.append({
                    "start": lunch_break_start,
                    "end": break_end,
                    "label": f"{lunch_break_start.strftime('%I:%M %p')} - {break_end.strftime('%I:%M %p')}",
                    "is_break": True,
                    "break_type": "Lunch Break"
                })
                
                current_time = break_end
                continue
            
            # Regular class slot
            time_slots.append({
                "start": current_time,
                "end": slot_end,
                "label": f"{current_time.strftime('%I:%M %p')} - {slot_end.strftime('%I:%M %p')}",
                "is_break": False
            })
            
            current_time = slot_end
        
        # Extract time slot labels for table headers
        time_headers = [slot["label"] for slot in time_slots]
        
        # Distribute classes properly across the available slots
        timed_schedule = {day: {} for day in parsed_schedule.keys()}
        
        for day, subjects_list in parsed_schedule.items():
            subject_index = 0
            for time_slot in time_slots:
                slot_label = time_slot["label"]
                
                if time_slot["is_break"]:
                    timed_schedule[day][slot_label] = time_slot["break_type"]
                else:
                    if subject_index < len(subjects_list):
                        timed_schedule[day][slot_label] = subjects_list[subject_index]
                        subject_index += 1
                    else:
                        timed_schedule[day][slot_label] = "Free"
        
        # Save timed schedule
        schedule_id = collection.insert_one({
            "input": {
                "total_subjects": total_subjects,
                "duration": duration,
                "classes_per_day": classes_per_day,
                "days_per_week": days_per_week,
                "subjects": subjects,
                "day_start_time": day_start_time,
                "day_end_time": day_end_time,
                "short_break_time": short_break_time,
                "lunch_break_time": lunch_break_time,
                "subject_preferences": subject_preferences if subject_preferences else None
            },
            "parsed_schedule": parsed_schedule,
            "timed_schedule": timed_schedule,
            "time_headers": time_headers
        }).inserted_id

        return render_template(
            "index.html", 
            schedule=timed_schedule, 
            time_headers=time_headers,
            schedule_id=schedule_id
        )

    return render_template("index.html")

if __name__ == "__main__":
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5001, debug=True)