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
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
                # --- Build professional HTML email body ---
                ref_id = f"HSV/{defaulter['reg_no']}/{defaulter['violation_datetime'][:10].replace('-', '')}"
                html_body = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background-color:#f0f2f5;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0f2f5;padding:30px 0;">
  <tr><td align="center">
    <table width="620" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:10px;overflow:hidden;">

      <!-- HEADER -->
      <tr><td style="background:#1a237e;padding:22px 28px 0 28px;">
        <table width="100%" cellpadding="0" cellspacing="0"><tr>
          <td width="52" valign="middle">
            <div style="width:48px;height:48px;background:#ffffff;border-radius:50%;text-align:center;line-height:48px;">
              <img src="https://img.icons8.com/ios-filled/50/1a237e/graduation-cap.png" width="28" height="28" style="margin-top:10px;" alt="Logo"/>
            </div>
          </td>
          <td style="padding-left:12px;" valign="middle">
            <div style="color:#ffffff;font-size:18px;font-weight:700;">VIT</div>
            <div style="color:#90caf9;font-size:11px;margin-top:2px;">Office of Campus Safety &amp; Compliance</div>
          </td>
          <td align="right" valign="middle">
            <div style="background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.4);border-radius:5px;padding:4px 12px;">
              <span style="color:#ffffff;font-size:10px;font-weight:700;letter-spacing:1px;">OFFICIAL NOTICE</span>
            </div>
          </td>
        </tr></table>
        <div style="background:#c62828;margin:14px -28px 0 -28px;padding:9px 28px;">
          <table width="100%" cellpadding="0" cellspacing="0"><tr>
            <td><span style="color:#ffffff;font-size:12px;font-weight:700;">HELMET SAFETY VIOLATION - FORMAL WARNING NOTICE</span></td>
            <td align="right"><span style="color:#ffcdd2;font-size:10px;">Ref: {ref_id}</span></td>
          </tr></table>
        </div>
      </td></tr>

      <!-- GREETING -->
      <tr><td style="padding:22px 28px 0 28px;">
        <p style="margin:0 0 5px;font-size:14px;color:#1a237e;font-weight:700;">Dear {defaulter['name']},</p>
        <p style="margin:0 0 18px;font-size:13px;color:#37474f;line-height:1.7;">
          Greetings from the <strong>Office of Campus Safety &amp; Compliance</strong>.<br/>
          This is a formal notice that a violation of the mandatory helmet safety regulation has been recorded against your name during routine campus surveillance on <strong style="color:#c62828;">{defaulter['violation_datetime']}</strong>.
        </p>
      </td></tr>

      <!-- VIOLATION DETAILS TABLE -->
      <tr><td style="padding:0 28px 18px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="border-radius:8px;overflow:hidden;border:1px solid #e3e8f0;">
          <tr><td colspan="2" style="background:#1a237e;padding:9px 16px;">
            <span style="color:#ffffff;font-size:11px;font-weight:700;letter-spacing:1px;">VIOLATION DETAILS</span>
          </td></tr>
          <tr style="background:#f5f7ff;"><td style="padding:9px 16px;font-size:12px;color:#546e7a;font-weight:600;width:42%;border-bottom:1px solid #e8ecf5;">Student Name</td><td style="padding:9px 16px;font-size:12px;color:#1a237e;font-weight:700;border-bottom:1px solid #e8ecf5;">{defaulter['name']}</td></tr>
          <tr><td style="padding:9px 16px;font-size:12px;color:#546e7a;font-weight:600;border-bottom:1px solid #e8ecf5;">Register Number</td><td style="padding:9px 16px;font-size:12px;color:#1a237e;font-weight:700;border-bottom:1px solid #e8ecf5;">{defaulter['reg_no']}</td></tr>
          <tr style="background:#f5f7ff;"><td style="padding:9px 16px;font-size:12px;color:#546e7a;font-weight:600;border-bottom:1px solid #e8ecf5;">Department</td><td style="padding:9px 16px;font-size:12px;color:#1a237e;font-weight:700;border-bottom:1px solid #e8ecf5;">{defaulter['department']}</td></tr>
          <tr><td style="padding:9px 16px;font-size:12px;color:#546e7a;font-weight:600;border-bottom:1px solid #e8ecf5;">Vehicle Number</td><td style="padding:9px 16px;font-size:12px;color:#1a237e;font-weight:700;border-bottom:1px solid #e8ecf5;">{defaulter['vehicle_no']}</td></tr>
          <tr style="background:#f5f7ff;"><td style="padding:9px 16px;font-size:12px;color:#546e7a;font-weight:600;border-bottom:1px solid #e8ecf5;">Date &amp; Time</td><td style="padding:9px 16px;font-size:12px;color:#c62828;font-weight:700;border-bottom:1px solid #e8ecf5;">{defaulter['violation_datetime']}</td></tr>
          <tr><td style="padding:9px 16px;font-size:12px;color:#546e7a;font-weight:600;border-bottom:1px solid #e8ecf5;">Violation Type</td><td style="padding:9px 16px;font-size:12px;color:#c62828;font-weight:700;border-bottom:1px solid #e8ecf5;">Riding without a helmet within campus premises</td></tr>
          <tr style="background:#fff8e1;"><td style="padding:9px 16px;font-size:12px;color:#546e7a;font-weight:600;">Notice Type</td>
          <td style="padding:9px 16px;"><span style="background:#c62828;color:#ffffff;font-size:10px;font-weight:700;padding:3px 10px;border-radius:12px;">FIRST &amp; FORMAL WARNING</span></td></tr>
        </table>
      </td></tr>

      <!-- POLICY NOTE -->
      <tr><td style="padding:0 28px 18px;">
        <div style="background:#e8eaf6;border-left:4px solid #1a237e;padding:12px 14px;">
          <p style="margin:0 0 3px;font-size:11px;font-weight:700;color:#1a237e;">CAMPUS SAFETY POLICY - SECTION 4.2</p>
          <p style="margin:0;font-size:12px;color:#37474f;line-height:1.6;">All students operating or riding a two-wheeler within college premises must wear a certified helmet at all times. Non-compliance is a violation of institutional safety rules.</p>
        </div>
      </td></tr>

      <!-- ACTION REQUIRED -->
      <tr><td style="padding:0 28px 18px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="border-radius:8px;overflow:hidden;border:1px solid #e3e8f0;">
          <tr><td style="background:#283593;padding:9px 16px;"><span style="color:#ffffff;font-size:11px;font-weight:700;letter-spacing:1px;">ACTION REQUIRED</span></td></tr>
          <tr><td style="padding:14px 16px;">
            <table cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td width="26" valign="top"><div style="background:#1a237e;color:#fff;font-size:10px;font-weight:700;width:20px;height:20px;border-radius:50%;text-align:center;line-height:20px;">1</div></td>
                <td style="font-size:12px;color:#37474f;padding-bottom:9px;line-height:1.6;padding-left:8px;">Ensure <strong>strict compliance</strong> with the helmet regulation effective immediately.</td>
              </tr>
              <tr>
                <td width="26" valign="top"><div style="background:#1a237e;color:#fff;font-size:10px;font-weight:700;width:20px;height:20px;border-radius:50%;text-align:center;line-height:20px;">2</div></td>
                <td style="font-size:12px;color:#37474f;padding-bottom:9px;line-height:1.6;padding-left:8px;">Report to the <strong>Campus Safety Office (Room No. 101, Admin Block)</strong> within <strong>3 working days</strong> to acknowledge this violation.</td>
              </tr>
              <tr>
                <td width="26" valign="top"><div style="background:#1a237e;color:#fff;font-size:10px;font-weight:700;width:20px;height:20px;border-radius:50%;text-align:center;line-height:20px;">3</div></td>
                <td style="font-size:12px;color:#37474f;line-height:1.6;padding-left:8px;">Carry a copy of this notice during your visit to the Safety Office.</td>
              </tr>
            </table>
          </td></tr>
        </table>
      </td></tr>

      <!-- CONSEQUENCES -->
      <tr><td style="padding:0 28px 18px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff3e0;border-radius:8px;border:1px solid #ffcc80;">
          <tr><td style="background:#e65100;padding:9px 16px;border-radius:7px 7px 0 0;">
            <span style="color:#ffffff;font-size:11px;font-weight:700;letter-spacing:1px;">CONSEQUENCES OF NON-COMPLIANCE</span>
          </td></tr>
          <tr><td style="padding:14px 16px;">
            <p style="margin:0 0 7px;font-size:12px;color:#bf360c;line-height:1.6;">&#9679; Escalation to the Head of Department and Disciplinary Committee.</p>
            <p style="margin:0 0 7px;font-size:12px;color:#bf360c;line-height:1.6;">&#9679; Suspension of vehicle entry permission to the campus.</p>
            <p style="margin:0;font-size:12px;color:#bf360c;line-height:1.6;">&#9679; Further disciplinary action as per institutional norms.</p>
          </td></tr>
        </table>
      </td></tr>

      <!-- SIGNATURE -->
      <tr><td style="padding:0 28px 22px;">
        <p style="margin:0 0 14px;font-size:12px;color:#37474f;line-height:1.7;">This notice is issued in the interest of your safety and well-being. We strongly urge you to take this matter seriously and act responsibly.</p>
        <div style="border-top:1px solid #e3e8f0;padding-top:14px;">
          <p style="margin:0 0 2px;font-size:13px;color:#1a237e;font-weight:700;">Campus Safety &amp; Compliance Officer</p>
          <p style="margin:0 0 2px;font-size:11px;color:#546e7a;">Office of Student Affairs | VIT</p>
          <p style="margin:0 0 2px;font-size:11px;color:#546e7a;">safety@college.edu | +91-XXXX-XXXXXX</p>
          <p style="margin:0;font-size:11px;color:#546e7a;">Mon-Fri, 9:00 AM - 5:00 PM</p>
        </div>
      </td></tr>

      <!-- FOOTER -->
      <tr><td style="background:#1a237e;padding:12px 28px;border-radius:0 0 10px 10px;">
        <p style="margin:0;font-size:10px;color:#90caf9;text-align:center;line-height:1.6;">
          This is a system-generated official notice. Please do not reply to this email.<br/>
          For queries, contact the Campus Safety Office as mentioned above.
        </p>
      </td></tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""

                print(f"Sending email to {defaulter['name']} at {defaulter['email_id']}...")

                # --- Send directly via Gmail API using MIME (avoids JSON parsing issues) ---
                subject = f"OFFICIAL NOTICE - Helmet Safety Violation | {defaulter['reg_no']} | {defaulter['violation_datetime']}"

                msg = MIMEMultipart("alternative")
                msg["To"] = defaulter['email_id']
                msg["Subject"] = subject
                msg.attach(MIMEText(html_body, "html"))

                raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
                send_result = api_resource.users().messages().send(
                    userId="me",
                    body={"raw": raw_message}
                ).execute()

                print(f"Email sent to {defaulter['email_id']} (id: {send_result.get('id')})")

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