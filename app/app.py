from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
import mysql.connector
import pandas as pd
import os
import csv
from langchain_community.agent_toolkits import GmailToolkit
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_community.tools.gmail.utils import (
    build_resource_service,
    get_gmail_credentials,
)
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'Your_API_KEY'  # Required for flash messages

# Base directory (project root)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "student"
}

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password'  # Change this for security

# File Paths
STUDENT_CSV_PATH = os.path.join(BASE_DIR, "students.csv")
DEFAULTERS_CSV_PATH = os.path.join(BASE_DIR, "matched_students.csv")

# Connect to MySQL Database
def connect_db():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as err:
        print(f"Database Connection Error: {err}")
        return None

# Create table if not exists
def init_db():
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_info (
                id INT AUTO_INCREMENT PRIMARY KEY,
                Name VARCHAR(255) NOT NULL,
                RegisterNum VARCHAR(50) UNIQUE NOT NULL,
                Department VARCHAR(100) NOT NULL,
                Bikeno VARCHAR(50) NOT NULL,
                MobileNum VARCHAR(15) NOT NULL,
                Email VARCHAR(255) UNIQUE NOT NULL,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
        connection.close()

# Initialize sent emails tracking table
def init_sent_emails_table():
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sent_violation_emails (
                id INT AUTO_INCREMENT PRIMARY KEY,
                Name VARCHAR(255) NOT NULL,
                RegisterNum VARCHAR(50) NOT NULL,
                Department VARCHAR(100) NOT NULL,
                Bikeno VARCHAR(50) NOT NULL,
                Email VARCHAR(255) NOT NULL,
                ViolationDateTime VARCHAR(50) NOT NULL,
                SentDateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                Status VARCHAR(50) DEFAULT 'Sent',
                UNIQUE KEY unique_violation (RegisterNum, ViolationDateTime)
            )
        """)
        connection.commit()
        connection.close()

# Initialize databases on startup
init_db()
init_sent_emails_table()

@app.route('/')
def home():
    return redirect(url_for('student_registration'))

@app.route('/register', methods=['GET', 'POST'])
def student_registration():
    if request.method == 'POST':
        connection = connect_db()
        if not connection:
            flash("Database connection failed", "error")
            return render_template('student_registration.html')
        
        try:
            cursor = connection.cursor()
            data = (
                request.form['name'],
                request.form['register_number'],
                request.form['department'],
                request.form['vehicle_number'],
                request.form['mobile_number'],
                request.form['email']
            )
            
            # Check if student already exists
            check_query = "SELECT * FROM student_info WHERE RegisterNum = %s OR Email = %s"
            cursor.execute(check_query, (request.form['register_number'], request.form['email']))
            existing_student = cursor.fetchone()
            
            if existing_student:
                flash("Student with this Register Number or Email already exists!", "error")
                return render_template('student_registration.html')
            
            query = """
            INSERT INTO student_info (Name, RegisterNum, Department, Bikeno, MobileNum, Email)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, data)
            connection.commit()
            
            flash(f"Student {request.form['name']} registered successfully!", "success")
            
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
        finally:
            if connection:
                connection.close()
                
        return redirect(url_for('student_registration'))

    return render_template('student_registration.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            flash("Login successful!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid username or password", "error")
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/student_details')
def student_details():
    connection = connect_db()
    if not connection:
        flash("Database connection failed", "error")
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT Name, RegisterNum as 'Register Number', Department, Bikeno, MobileNum, Email FROM student_info ORDER BY Name"
        cursor.execute(query)
        students = cursor.fetchall()
        
        # Get unique departments for filter
        dept_query = "SELECT DISTINCT Department FROM student_info ORDER BY Department"
        cursor.execute(dept_query)
        departments = [dept['Department'] for dept in cursor.fetchall()]
        
        return render_template('student_details.html', students=students, departments=departments)
    except Exception as e:
        flash(f"Error fetching student details: {str(e)}", "error")
        return redirect(url_for('admin_dashboard'))
    finally:
        if connection:
            connection.close()

@app.route('/get_student/<reg_no>')
def get_student(reg_no):
    connection = connect_db()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT Name, RegisterNum as 'Register Number', Department, Bikeno, MobileNum, Email FROM student_info WHERE RegisterNum = %s"
        cursor.execute(query, (reg_no,))
        student = cursor.fetchone()
        
        if student:
            return jsonify(student)
        else:
            return jsonify({"error": "Student not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/update_student', methods=['POST'])
def update_student():
    if request.method == 'POST':
        connection = connect_db()
        if not connection:
            flash("Database connection failed", "error")
            return redirect(url_for('student_details'))
        
        try:
            cursor = connection.cursor()
            data = (
                request.form['name'],
                request.form['department'],
                request.form['vehicle_number'],
                request.form['mobile_number'],
                request.form['email'],
                request.form['register_number']
            )
            
            query = """
            UPDATE student_info 
            SET Name = %s, Department = %s, Bikeno = %s, MobileNum = %s, Email = %s 
            WHERE RegisterNum = %s
            """
            cursor.execute(query, data)
            connection.commit()
            
            if cursor.rowcount > 0:
                flash(f"Student {request.form['name']} updated successfully!", "success")
            else:
                flash("No changes were made to the student record", "info")
                
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
        except Exception as e:
            flash(f"Error updating student: {str(e)}", "error")
        finally:
            if connection:
                connection.close()
        
        return redirect(url_for('student_details'))

@app.route('/delete_student/<reg_no>', methods=['POST'])
def delete_student(reg_no):
    connection = connect_db()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = connection.cursor()
        # First get student name for flash message
        cursor.execute("SELECT Name FROM student_info WHERE RegisterNum = %s", (reg_no,))
        student = cursor.fetchone()
        
        if not student:
            return jsonify({"error": "Student not found"}), 404
        
        # Delete the student
        query = "DELETE FROM student_info WHERE RegisterNum = %s"
        cursor.execute(query, (reg_no,))
        connection.commit()
        
        return jsonify({"success": True, "message": f"Student {student[0]} deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/download_students')
def download_students():
    connection = connect_db()
    if not connection:
        flash("Database connection failed", "error")
        return redirect(url_for('admin_dashboard'))
    
    try:
        query = "SELECT Name, RegisterNum as 'Register Number', Department, Bikeno as 'Vehicle Number', MobileNum as 'Mobile Number', Email, registration_date as 'Registration Date' FROM student_info"
        df = pd.read_sql(query, connection)
        df.to_csv(STUDENT_CSV_PATH, index=False)
        flash("Students data downloaded successfully!", "success")
        connection.close()
        return send_file(STUDENT_CSV_PATH, as_attachment=True, download_name="student_registrations.csv")
    except Exception as e:
        flash(f"Error downloading data: {str(e)}", "error")
        return redirect(url_for('admin_dashboard'))

@app.route('/defaulters')
def defaulters():
    new_defaulters = []
    sent_defaulters = []
    
    if os.path.exists(DEFAULTERS_CSV_PATH):
        try:
            with open(DEFAULTERS_CSV_PATH, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Get all sent violations from database
                connection = connect_db()
                sent_violations = {}
                if connection:
                    cursor = connection.cursor()
                    cursor.execute("SELECT RegisterNum, ViolationDateTime FROM sent_violation_emails")
                    for row in cursor.fetchall():
                        key = f"{row[0]}_{row[1]}"
                        sent_violations[key] = True
                    connection.close()
                
                # Categorize defaulters
                for row in reader:
                    key = f"{row['Register Number']}_{row['Date/Time']}"
                    if key in sent_violations:
                        sent_defaulters.append(row)
                    else:
                        new_defaulters.append(row)
            
            # Flash messages with counts
            if new_defaulters:
                flash(f"Found {len(new_defaulters)} new defaulter(s) pending email", "info")
            if sent_defaulters:
                flash(f"{len(sent_defaulters)} defaulter(s) have already received emails", "success")
            if not new_defaulters and not sent_defaulters:
                flash("No defaulters found in the file", "info")
                
        except Exception as e:
            flash(f"Error reading defaulters file: {str(e)}", "error")
    else:
        flash("Defaulters file not found", "warning")
    
    return render_template('defaulters.html', 
                         new_defaulters=new_defaulters, 
                         sent_defaulters=sent_defaulters)

@app.route('/send_violation_emails', methods=['POST'])
def send_violation_emails():
    try:
        result = send_violation_mails()
        if "successfully" in result.lower():
            flash("Violation emails sent successfully!", "success")
        else:
            flash(result, "warning")
        return redirect(url_for('defaulters'))
    except Exception as e:
        flash(f"Error sending emails: {str(e)}", "error")
        return redirect(url_for('defaulters'))

@app.route('/sent_emails_history')
def sent_emails_history():
    """View history of all sent violation emails"""
    connection = connect_db()
    if not connection:
        flash("Database connection failed", "error")
        return redirect(url_for('defaulters'))
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT Name, RegisterNum, Department, Bikeno, Email, 
                   ViolationDateTime, SentDateTime, Status 
            FROM sent_violation_emails 
            ORDER BY SentDateTime DESC
        """
        cursor.execute(query)
        sent_emails = cursor.fetchall()
        return render_template('sent_emails_history.html', sent_emails=sent_emails)
    except Exception as e:
        flash(f"Error fetching sent emails history: {str(e)}", "error")
        return redirect(url_for('defaulters'))
    finally:
        if connection:
            connection.close()

# ----------------- EMAIL SENDING FUNCTION -----------------

def send_violation_mails(defaulters_filename=os.path.join(BASE_DIR, 'matched_students.csv')):
    """
    Send violation emails to defaulters using Gmail API and LangChain
    """
    try:
        # Check if credentials exist
        creds_path = os.path.join(BASE_DIR, "cred.json")
        token_path = os.path.join(BASE_DIR, "token.json")
        
        if not os.path.exists(creds_path):
            return "Gmail credentials file (cred.json) not found. Please set up Gmail API credentials."
        
        # Get Gmail credentials
        credentials = get_gmail_credentials(
            token_file=token_path,
            scopes=["https://mail.google.com/"],
            client_secrets_file=creds_path,
        )

        # Build API resource
        api_resource = build_resource_service(credentials=credentials)
        toolkit = GmailToolkit(api_resource=api_resource)
        tools = toolkit.get_tools()

        # Initialize LLM
        llm = ChatGroq(
            model="openai/gpt-oss-120b",
            api_key="Your_API_KEY",
            temperature=0.1
        )

        agent_executor = create_react_agent(llm, tools)

        # Ensure the defaulters CSV exists
        if not os.path.exists(defaulters_filename):
            return f"Defaulters file not found: {defaulters_filename}"

        emails_sent = 0
        emails_failed = 0
        already_sent = 0
        new_defaulters = []

        # First, read all defaulters from CSV
        with open(defaulters_filename, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            try:
                header = next(reader)
            except StopIteration:
                return "Defaulters file is empty"
            
            # Extract column indices
            try:
                name_index = header.index("Name")
                reg_no_index = header.index("Register Number")
                vehicle_no_index = header.index("Vehicle Number")
                dept_index = header.index("Department")
                email_index = header.index("Email")
                datetime_index = header.index("Date/Time")
            except ValueError as e:
                return f"Missing expected column in defaulters CSV: {e}"
            
            for row in reader:
                try:
                    if len(row) <= max(name_index, reg_no_index, vehicle_no_index, dept_index, email_index, datetime_index):
                        print(f"Skipping incomplete row: {row}")
                        emails_failed += 1
                        continue
                    
                    name = row[name_index]
                    reg_no = row[reg_no_index]
                    vehicle_no = row[vehicle_no_index]
                    department = row[dept_index]
                    email_id = row[email_index]
                    violation_datetime = row[datetime_index]
                    
                    if not all([name, reg_no, email_id]):
                        print(f"Skipping row with missing required data: {row}")
                        emails_failed += 1
                        continue
                    
                    # Check if this violation email has already been sent
                    connection = connect_db()
                    if connection:
                        cursor = connection.cursor()
                        check_query = "SELECT id FROM sent_violation_emails WHERE RegisterNum = %s AND ViolationDateTime = %s"
                        cursor.execute(check_query, (reg_no, violation_datetime))
                        existing = cursor.fetchone()
                        
                        if existing:
                            already_sent += 1
                            connection.close()
                            continue
                        connection.close()
                    
                    # Store defaulter info for later processing
                    new_defaulters.append({
                        'name': name,
                        'reg_no': reg_no,
                        'vehicle_no': vehicle_no,
                        'department': department,
                        'email_id': email_id,
                        'violation_datetime': violation_datetime
                    })
                    
                except Exception as e:
                    print(f"Error processing row: {e}")
                    emails_failed += 1

        # Send emails to new defaulters
        for defaulter in new_defaulters:
            try:
                violation_query = f'''
                Send an email to {defaulter['email_id']} with the following details:
                
                Subject: Helmet Rule Violation Notice - {defaulter['violation_datetime']}
                
                Dear {defaulter['name']},
                
                This is to inform you that you have been identified as not wearing a helmet on {defaulter['violation_datetime']}.
                
                Student Details:
                - Register Number: {defaulter['reg_no']}
                - Department: {defaulter['department']}
                - Vehicle Number: {defaulter['vehicle_no']}
                
                Please note that wearing a helmet is mandatory as per college safety regulations. This is a warning notice. 
                Repeat offenses may lead to stricter disciplinary action.
                
                We request you to comply with the safety rules for your own protection.
                
                Regards,
                College Safety Department
                
                Directly send this email without asking for review or confirmation.
                '''
                
                print(f"Sending email to {defaulter['name']} at {defaulter['email_id']}...")
                
                events = agent_executor.stream(
                    {"messages": [("user", violation_query)]},
                    stream_mode="values",
                )
                
                # Process events
                for event in events:
                    if "messages" in event and event["messages"]:
                        print(f"Email sent to {defaulter['email_id']}")
                
                # Record in database that email was sent
                connection = connect_db()
                if connection:
                    cursor = connection.cursor()
                    insert_query = """
                    INSERT INTO sent_violation_emails 
                    (Name, RegisterNum, Department, Bikeno, Email, ViolationDateTime, Status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (
                        defaulter['name'], 
                        defaulter['reg_no'], 
                        defaulter['department'], 
                        defaulter['vehicle_no'], 
                        defaulter['email_id'], 
                        defaulter['violation_datetime'],
                        'Sent'
                    ))
                    connection.commit()
                    connection.close()
                
                emails_sent += 1
                
            except Exception as e:
                print(f"Failed to send email for {defaulter['name']}: {e}")
                emails_failed += 1

        result_msg = f"Process completed. New emails sent: {emails_sent}, Already sent: {already_sent}, Failed: {emails_failed}"
        print(result_msg)
        return result_msg
        
    except Exception as e:
        error_msg = f"Error in email sending function: {str(e)}"
        print(error_msg)
        return error_msg

@app.route('/api/students/count')
def get_student_count():
    """API endpoint to get total student count"""
    connection = connect_db()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM student_info")
        count = cursor.fetchone()[0]
        return jsonify({"count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/students/departments')
def get_department_stats():
    """API endpoint to get department-wise statistics"""
    connection = connect_db()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT Department, COUNT(*) as count 
            FROM student_info 
            GROUP BY Department 
            ORDER BY count DESC
        """)
        stats = cursor.fetchall()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/search_students')
def search_students():
    """Search students by name, register number, or department"""
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])
    
    connection = connect_db()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        search_query = """
            SELECT Name, RegisterNum, Department, Bikeno, MobileNum, Email 
            FROM student_info 
            WHERE Name LIKE %s OR RegisterNum LIKE %s OR Department LIKE %s OR Bikeno LIKE %s
            LIMIT 10
        """
        search_term = f"%{query}%"
        cursor.execute(search_query, (search_term, search_term, search_term, search_term))
        results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    flash("Page not found", "error")
    return redirect(url_for('home'))

@app.errorhandler(500)
def internal_error(error):
    flash("Internal server error", "error")
    return redirect(url_for('home'))

if __name__ == '__main__':
    # Create necessary directories if they don't exist
    os.makedirs(BASE_DIR, exist_ok=True)
    
    # Initialize databases
    init_db()
    init_sent_emails_table()
    
    # Run the app
    app.run(port=5001, debug=True)