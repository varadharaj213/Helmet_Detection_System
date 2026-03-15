import csv
import datetime
from database import connect_db

def fetch_student_data(vehicle_number):
    connection = connect_db()
    if not connection:
        return None

    cursor = connection.cursor()
    query = """
        SELECT Name, RegisterNum, Bikeno, Department, Email, MobileNum
        FROM student_info
        WHERE Bikeno = %s
    """
    cursor.execute(query, (vehicle_number,))
    result = cursor.fetchone()
    connection.close()
    return result

def process_vehicle_data():
    input_csv = "extracted_number_plates.csv"
    output_csv = "matched_students.csv"
    matched_data = []

    try:
        with open(input_csv, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                _, vehicle_number, date_time = row
                student = fetch_student_data(vehicle_number)
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
            writer.writerow(["Name", "Register Number", "Vehicle Number", "Department", "Email", "Mobile Number", "Date/Time"])
            writer.writerows(matched_data)
        print(f"Matched data saved to '{output_csv}'.")
    else:
        print("No matches found.")

if __name__ == "__main__":
    process_vehicle_data()
