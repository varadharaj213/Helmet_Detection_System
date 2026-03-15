import mysql.connector
import csv
from datetime import datetime

def connect_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="student"
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def check_table_exists(connection, table_name):
    cursor = connection.cursor()
    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
    result = cursor.fetchone()
    return result is not None

def fetch_student_data(connection, vehicle_number):
    cursor = connection.cursor()
    query = """
        SELECT Name, RegisterNum, Bikeno, Department, Email
        FROM student_info
        WHERE Bikeno = %s
    """
    cursor.execute(query, (vehicle_number,))
    return cursor.fetchone()

def process_vehicle_data():
    connection = connect_db()
    if not connection:
        return
    
    if not check_table_exists(connection, "student_info"):
        print("Table 'student_info' does not exist.")
        return
    
    input_csv = "extracted_text.csv"
    output_csv = "matched_students.csv"
    matched_data = []
    
    try:
        with open(input_csv, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                _, vehicle_number, date_time = row
                student = fetch_student_data(connection, vehicle_number)
                if student:
                    student_with_time = student + (date_time,)
                    matched_data.append(student_with_time)
                    print(f"Match found: {student_with_time}")
    except FileNotFoundError:
        print(f"File '{input_csv}' not found.")
        return
    
    if matched_data:
        with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "Register Number", "Vehicle Number", "Department", "Email", "Date/Time"])
            writer.writerows(matched_data)
        print(f"Matched data saved to '{output_csv}'.")
    else:
        print("No matches found.")
    
    connection.close()

if __name__ == "__main__":
    process_vehicle_data()
