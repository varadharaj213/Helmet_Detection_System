import streamlit as st
import subprocess
import os
import signal
import psutil
import time

# Change this path to the actual folder where your scripts and images are located
SCRIPT_DIR = r"D:\HELMET_DETECTION_PROJECT\Helmet-Detection-System"
IMAGES_DIR = os.path.join(SCRIPT_DIR, "number_plates")

# Initialize session state for process tracking
if 'processes' not in st.session_state:
    st.session_state.processes = {}
if 'process_status' not in st.session_state:
    st.session_state.process_status = {}

def kill_process_tree(pid):
    """Kill a process and all its children."""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.kill()
        parent.kill()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

def run_script(script_name):
    """Runs a Python script and displays its output."""
    try:
        script_path = os.path.join(SCRIPT_DIR, script_name)
        
        # Start the process
        process = subprocess.Popen(
            ["python", script_path],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        # Store the process
        st.session_state.processes[script_name] = process
        st.session_state.process_status[script_name] = "running"
        
        # Create placeholder for output
        output_placeholder = st.empty()
        stop_button_placeholder = st.empty()
        
        # Display stop button
        if stop_button_placeholder.button(f"Stop {script_name}", key=f"stop_{script_name}"):
            kill_process_tree(process.pid)
            st.session_state.process_status[script_name] = "stopped"
            st.rerun()
        
        # Read output in real-time
        output_text = ""
        while process.poll() is None:
            # Read stdout
            stdout_line = process.stdout.readline()
            if stdout_line:
                output_text += stdout_line
                output_placeholder.text_area(f"Output - {script_name}", output_text, height=300)
            
            # Read stderr
            stderr_line = process.stderr.readline()
            if stderr_line:
                output_text += stderr_line
                output_placeholder.text_area(f"Output - {script_name}", output_text, height=300)
            
            # Check if stop was requested
            if st.session_state.process_status.get(script_name) == "stopped":
                kill_process_tree(process.pid)
                break
            
            time.sleep(0.1)
        
        # Get remaining output
        stdout, stderr = process.communicate()
        if stdout:
            output_text += stdout
        if stderr:
            output_text += stderr
        
        # Final output
        if st.session_state.process_status.get(script_name) == "stopped":
            st.warning(f"{script_name} was stopped by user")
        else:
            output_placeholder.text_area(f"Output - {script_name}", output_text, height=300)
            st.success(f"{script_name} completed!")
        
        # Clean up
        del st.session_state.processes[script_name]
        del st.session_state.process_status[script_name]
        
    except Exception as e:
        st.error(f"Error running {script_name}: {str(e)}")
        if script_name in st.session_state.processes:
            del st.session_state.processes[script_name]
        if script_name in st.session_state.process_status:
            del st.session_state.process_status[script_name]

def show_defaulters_images():
    """Displays images from the 'images' folder."""
    if os.path.exists(IMAGES_DIR):
        image_files = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if image_files:
            st.subheader("Defaulters' Number Plates:")
            
            # Create columns for better layout
            cols = st.columns(3)
            for idx, image_file in enumerate(image_files):
                with cols[idx % 3]:
                    image_path = os.path.join(IMAGES_DIR, image_file)
                    st.image(image_path, caption=image_file, use_container_width=True)
        else:
            st.warning("No images found in the 'images' folder.")
    else:
        st.error(f"Images folder not found: {IMAGES_DIR}")

def stop_process(script_name):
    """Stop a running process."""
    if script_name in st.session_state.processes:
        process = st.session_state.processes[script_name]
        kill_process_tree(process.pid)
        st.session_state.process_status[script_name] = "stopped"
        st.success(f"Stopped {script_name}")
        st.rerun()

# Main UI
st.title("Video Processing Dashboard")

# Display currently running processes
if st.session_state.processes:
    st.sidebar.header("Running Processes")
    for script_name in list(st.session_state.processes.keys()):
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            st.write(f"🟢 {script_name}")
        with col2:
            if st.button("Stop", key=f"sidebar_stop_{script_name}"):
                stop_process(script_name)

# Main buttons
col1, col2 = st.columns(2)

with col1:
    if st.button("Process Video", disabled="main.py" in st.session_state.processes):
        run_script("main.py")

with col2:
    if st.button("Live Camera to Detect", disabled="webcam_main.py" in st.session_state.processes):
        run_script("webcam_main.py")

col3, col4 = st.columns(2)

with col3:
    if st.button("Extract Helmet Defaulters Vehicle Number", disabled="extracting.py" in st.session_state.processes):
        run_script("extracting.py")

with col4:
    if st.button("Check with Student Record and Save", disabled="platefinder.py" in st.session_state.processes):
        run_script("platefinder.py")

# Separate button for showing images (non-process task)
if st.button("Show Defaulters' Number Plates"):
    show_defaulters_images()

# Add a refresh button to check process status
if st.sidebar.button("Refresh Status"):
    st.rerun()