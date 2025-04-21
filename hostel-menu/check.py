import sqlite3

def select_housekeeping_companies():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()

    # Check if the table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='housekeeping_companies';")
    table_exists = c.fetchone()
    
    if table_exists:
        print(f"Table {table_exists[0]} found.")
        
        # Select all data from the housekeeping_companies table
        c.execute('SELECT * FROM housekeeping_companies')
        rows = c.fetchall()
        
        if rows:
            for row in rows:
                print(row)
        else:
            print("The housekeeping_companies table is empty.")
    else:
        print("The table 'housekeeping_companies' does not exist.")
    
    conn.close()

# Call the function to select and print the table data
select_housekeeping_companies()
