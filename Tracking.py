import streamlit as st
import cv2
import face_recognition as frg
import yaml 
import requests
import time
from utils import recognize, build_dataset

# Streamlit page setup
st.set_page_config(layout="wide")

# Load config
cfg = yaml.load(open('config.yaml', 'r'), Loader=yaml.FullLoader)
PICTURE_PROMPT = cfg['INFO']['PICTURE_PROMPT']
WEBCAM_PROMPT = cfg['INFO']['WEBCAM_PROMPT']

# ---- STEP 1: Wait for Hardware Response ----
def get_hardware_status():
    try:
        response = requests.get("https://aeprojecthub.in/getdata.php?id=2&C=F1", timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        st.error(f"Error checking hardware status: {e}")
    return None

st.title("🔁 Checking Hardware Status")

placeholder = st.empty()
with placeholder.container():
    with st.spinner("⏳ Waiting for hardware response..."):
        while True:
            status = get_hardware_status()
            if status == "1":
                break
            time.sleep(2)

# Clear loading UI
placeholder.empty()
st.success("✅ Hardware Ready")

# ---- STEP 2: Main Face Recognition App ----

st.sidebar.title("Settings")

# Menu bar
menu = ["Picture", "Webcam"]
choice = st.sidebar.selectbox("Input type", menu)

# Tolerance slider
TOLERANCE = st.sidebar.slider("Tolerance", 0.0, 1.0, 0.5, 0.01)
st.sidebar.info("Lower tolerance = stricter matching. Higher = more lenient.")

# Student Info display
st.sidebar.title("Student Information")
name_container = st.sidebar.empty()
id_container = st.sidebar.empty()
name_container.info('Name: Unknown')
id_container.success('ID: Unknown')

# Match flag tracking
previous_match = None

# Send GET request based on match
def send_match_status(match_found: bool):
    global previous_match
    x = "1" if match_found else "0"
    if str(previous_match) != x:
        try:
            url = f"https://aeprojecthub.in/flagChange.php?f5=1&f1={x}"
            response = requests.get(url)
            if response.status_code == 200:
                print(f"Status sent: {x}")
            else:
                print(f"Failed to send status: {response.status_code}")
        except Exception as e:
            print(f"Error sending status: {e}")
        previous_match = x

# Picture mode
if choice == "Picture":
    st.title("📷 Face Recognition - Picture")
    st.write(PICTURE_PROMPT)
    uploaded_images = st.file_uploader("Upload Images", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)

    if uploaded_images:
        for image in uploaded_images:
            image = frg.load_image_file(image)
            image, name, id = recognize(image, TOLERANCE)
            name_container.info(f"Name: {name}")
            id_container.success(f"ID: {id}")
            st.image(image)

            match_found = name != "Unknown"
            send_match_status(match_found)
    else:
        st.info("📂 Please upload an image.")

# Webcam mode
elif choice == "Webcam":
    st.title("🎥 Face Recognition - Webcam")
    st.write(WEBCAM_PROMPT)

    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    FRAME_WINDOW = st.image([])

    while True:
        ret, frame = cam.read()
        if not ret:
            st.error("❌ Failed to capture frame from camera")
            st.info("🛑 Please close other camera apps and restart.")
            st.stop()

        image, name, id = recognize(frame, TOLERANCE)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        name_container.info(f"Name: {name}")
        id_container.success(f"ID: {id}")
        FRAME_WINDOW.image(image)

        match_found = name != "Unknown"
        send_match_status(match_found)

# Developer: rebuild dataset
with st.sidebar.form(key='my_form'):
    st.title("🛠️ Developer Section")
    submit_button = st.form_submit_button(label='REBUILD DATASET')
    if submit_button:
        with st.spinner("Rebuilding dataset..."):
            build_dataset()
        st.success("✅ Dataset has been rebuilt")
