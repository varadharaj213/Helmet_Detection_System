import os
import pytesseract
from PIL import Image
import csv
import re
from datetime import datetime

# Set Tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = r'c:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path)
        # Pre-processing for clearer images
        image = image.resize((image.width * 2, image.height * 2))
        image = image.convert("L")
        extracted_text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')
        # Remove spaces and special characters to format as a single string
        cleaned_text = re.sub(r'[^A-Za-z0-9]', '', extracted_text)
        return cleaned_text.strip()
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

def get_image_datetime(image_path):
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        if exif_data and 36867 in exif_data:
            datetime_str = exif_data[36867]
            return datetime.strptime(datetime_str, "%Y:%m:%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"Error getting date/time for {image_path}: {e}")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def process_images_in_folder(folder_path, output_csv):
    image_extensions = ('.png', '.jpg', '.jpeg')
    extracted_data = []

    print("\nExtracted Data:\n")
    print(f"{'Image Name':<30} {'Number Plate':<20} {'Date/Time'}")
    print("=" * 80)

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(image_extensions):
            image_path = os.path.join(folder_path, filename)
            text = extract_text_from_image(image_path)
            timestamp = get_image_datetime(image_path)
            if text:
                extracted_data.append([filename, text, timestamp])
                print(f"{filename:<30} {text:<20} {timestamp}")  # Display in command prompt
    
    # Save extracted text to CSV
    with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Image Name", "Number Plate", "Date/Time"])
        writer.writerows(extracted_data)

    print("\nExtraction completed. Results saved in", output_csv)

if __name__ == "__main__":
    folder_path = r"D:\Helemtworkingproject\Helmet-Detection-System\number_plates"
    output_csv = r"D:\Helemtworkingproject\Helmet-Detection-System\extracted_text.csv"
    process_images_in_folder(folder_path, output_csv)
