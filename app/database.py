import mysql.connector
from config import DATABASE_CONFIG

def connect_db():
    try:
        connection = mysql.connector.connect(**DATABASE_CONFIG)
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def fetch_all_students():
    connection = connect_db()
    if not connection:
        return []

    cursor = connection.cursor()
    cursor.execute("SELECT Name, RegisterNum, Department, Bikeno, MobileNum FROM student_info")
    students = cursor.fetchall()
    connection.close()
    return students

def insert_student(name, regno, department, vehicle_number, mobile, email):
    connection = connect_db()
    if not connection:
        return False

    cursor = connection.cursor()
    query = """
    INSERT INTO student_info (Name, RegisterNum, Department, Bikeno, MobileNum, Email)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(query, (name, regno, department, vehicle_number, mobile, email))
        connection.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return False
    finally:
        connection.close()
