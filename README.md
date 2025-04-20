# university-services-management-website
A university services management website for hostel services, housekeeping services, and AI-powered smart tools for service management and education. Done as a part of Cloud Computing course project at PES University.

Repository link: `https://github.com/adyabhat/university-services-management-website`.

Contributors:
1. Adya Bhat
2. Anagha Kini
3. Chandana B S
4. Arpitha Venugopal
5. Chaitra V
6. Vidhatri V
All contributors belong to section 6A (CSE-AIML), PES University- Ring Road Campus (Even semester, 2025).

Microservices Integrated:
A. Hostel Management Services:
    1. Hostel Student Registration, Deletion, Display
    2. Hostel Attendance Marking and Attendance History Display
    3. Hostel Mess Menu Display and Updation, Integration
B. Housekeeping Services:
    4. Services Registration, Updation and Provision for Feedback
C. AI-Powered Smart Tools:
    5. Intelligent Course Scheduler (timetable)
    6. Smart Content Recommender (for topics, to use as a study guide)

Tech Stack Used:
1. Flask: Flask is used as the web framework to create backend logic for routing, handling HTTP requests, and integrating with templates.
2. Python: Python is the core programming language used to write all backend logic, including Flask routes and database operations.
3. Sqlite3: SQLite3 is used as the lightweight, serverless relational database engine to store and manage application-specific data like student registrations, attendance records, housekeeping feedback, and menu schedules within each Flask service using .db files.
4. HTML: HTML is used to structure the web pages rendered by Flask templates. 
5. CSS (Vanilla CSS, Bootstrap CSS): CSS, including both vanilla CSS and Bootstrap CSS, is used to style the user interface for responsiveness and consistent layout. 
6. Javascript: JavaScript is used to add interactivity and client-side functionality to enhance the user experience on the web pages. 
7. Docker: Docker is used to containerize the application, enabling each service such as hostel management and course management to run in isolated environments on specific ports.

Project Folder Structure:
```
university-management/
│
├── docker-compose.yml
│
├── hostelmgmt-housekeeping/
│   ├── templates/
│   │   ├── attendance.html
│   │   ├── attendance_history.html
│   │   ├── attendance_history_results.html
│   │   ├── hostel-index.html
│   │   ├── housekeeping-feedback.html
│   │   ├── housekeeping-index.html
│   │   ├── housekeeping-register.html
│   │   ├── housekeeping-upgrade.html
│   │   ├── index.html
│   │   ├── menu.html
│   │   ├── register.html
│   │   └── students.html
│   ├── venv/
│   ├── app.py
│   ├── check.py
│   ├── Dockerfile
│   ├── hostel.db
│   ├── students.db
│   ├── requirements.txt
│   └── README.txt
│
├── intelligent-scheduler/
│   ├── templates/
│   │   └── index.html
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
└── smart-content-recommender/
    ├── static/
    ├── templates/
    │   ├── history.html
    │   └── index.html
    ├── app.py
    ├── Dockerfile
    └── requirements.txt
```

Integration of Microservices:
The first 4 microservices (hostel management and housekeeping domains) listed above were integrated into a common web app. Database operations (retrieval, storage and updates) were made independent by using distinct function calls for modularity. Front end pages and components were meticulously organized to improve design. This web app, along with the 2 microservices of the smart university domain, were each deployed on Docker containers. They were designed to be accessible through the front end, but each of which was deployed on a different Docker container. This was set up through Docker Compose. Thus a multi-container application was built, entirely configured through a single YAML file.

Running The Website:
1. Clone this repository and navigate to the `university-management` folder.
2. Build the Docker containers and set it up by running `docker-compose up --build`.
3. Open the web app on the browser through the following URLs:
   Hostel and Housekeeping: http://localhost:5000
   Intelligent Course Scheduler: http://localhost:5001
   Smart Content Recommender: http://localhost:5002
