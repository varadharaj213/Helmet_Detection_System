import streamlit as st
import subprocess
import os

# Change this path to the actual folder where your scripts and images are located
SCRIPT_DIR = r"D:\Helemtworkingproject\Helmet-Detection-System"
IMAGES_DIR = os.path.join(SCRIPT_DIR, "number_plates")

def run_script(script_name):
    """Runs a Python script and displays its output."""
    try:
        script_path = os.path.join(SCRIPT_DIR, script_name)
        result = subprocess.run(["python", script_path], shell=True, capture_output=True, text=True)
        st.text_area("Output", result.stdout + result.stderr, height=300)
    except Exception as e:
        st.error(f"Error running {script_name}: {str(e)}")

def show_defaulters_images():
    """Displays images from the 'images' folder."""
    if os.path.exists(IMAGES_DIR):
        image_files = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if image_files:
            st.subheader("Defaulters' Number Plates:")
            for image_file in image_files:
                image_path = os.path.join(IMAGES_DIR, image_file)
                st.image(image_path, caption=image_file, use_container_width=True)  # Updated parameter
        else:
            st.warning("No images found in the 'images' folder.")
    else:
        st.error(f"Images folder not found: {IMAGES_DIR}")

st.title("Video Processing Dashboard")

if st.button("Process Video"):
    run_script("main.py")

if st.button("Show Defaulters' Number Plates"):
    show_defaulters_images()


if st.button("Extract Helmet Defaulters Vehicle Number"):
    run_script("extracting.py")

if st.button("Check with Student Record and Save"):
    run_script("platefinder.py")

