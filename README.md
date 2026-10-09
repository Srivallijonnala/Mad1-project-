Placement Portal Application

A role-based campus placement management web application built with Flask. It connects three types of users, the Admin (Institute), Companies, and Students, on one platform so placement drives can be created, approved, applied to, and tracked in one place.

Developed as the MAD 1 (Modern Application Development 1) project for the IIT Madras BS Degree Program, January 2026 term.

Features
Admin (Institute)
Approve or reject company registrations
Manage students and companies, including blacklisting or deactivating accounts
Oversee placement drives and student applications across the portal
Company
Register and create a company profile (HR contact, website, industry, description)
Create and manage placement drives with job title, description, package, location, and application deadline
View student applications for each drive and update their status
Student
Register and build a profile (roll number, branch, graduation year, bio, resume)
Browse available placement drives
Apply to drives with a cover note
Track the status of every application
General
Secure login and session handling with role-based access control
Separate dashboards for each role
Clean, responsive interface built with Bootstrap
Tech Stack
Layer	Technology
Backend framework	Flask
Database	SQLite
ORM	SQLAlchemy
Authentication	Flask-Login
Frontend	HTML, CSS, Bootstrap
Templating	Jinja2
Database Design

The schema has five main tables: User, Student, Company, PlacementDrive, and Application.

User to Student: one-to-one
User to Company: one-to-one
Company to PlacementDrive: one-to-many
Student to Application: one-to-many
PlacementDrive to Application: one-to-many
Project Structure
Placement_Portal_Application/
├── app.py          # Application entry point: initializes extensions, registers blueprints
├── models/         # SQLAlchemy models (User, Student, Company, PlacementDrive, Application)
├── routes/         # Blueprints for admin, student, and company functionality
├── templates/      # Jinja2 HTML templates
├── static/         # CSS and other static assets
└── requirements.txt
Getting Started
Clone the repository
   git clone https://github.com/Srivallijonnala/Mad1-project-.git
   cd Mad1-project-
Create and activate a virtual environment
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Mac/Linux
Install dependencies
   pip install -r requirements.txt
Run the application
   python app.py
Open http://127.0.0.1:5000 in your browser.
Demo Video

Watch the project walkthrough

AI / LLM Declaration

Claude.ai was used to improve documentation wording and clarify certain backend concepts. ChatGPT-5 was used to generate basic frontend button and div code, which was reviewed and integrated manually. The core implementation, database design, debugging, and system integration were done independently by the author.

Author

Srivalli Jonnala Standalone student, IIT Madras BS Degree Program Interested in web development, especially Flask and backend technologies.
