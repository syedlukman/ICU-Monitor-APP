import streamlit as st
import pandas as pd
import numpy as np
import time
import base64
import main
import os

# -------------------------------
# Page Config & Styling
# -------------------------------
st.set_page_config(page_title="Real-Time ICU Monitor", layout="wide")

# Custom CSS for stylish dashboard
st.markdown("""
<style>
.main {
    background-color: #0b1e2d;
    color: white;
    font-family: 'Poppins', sans-serif;
}
h1 {
    color: #00e6e6;
    text-align: center;
    font-size: 2.8rem;
}
.stButton>button {
    background-color: #0077ff;
    color: white;
    border-radius: 8px;
    font-weight: bold;
    transition: 0.3s;
}
.stButton>button:hover {
    background-color: #00e6e6;
    color: black;
}
.status-card {
    background-color: #142b3b;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 0px 10px #00e6e6;
    text-align: center;
    margin-bottom: 15px;
}
.pulse {
    animation: heartbeat 1.5s infinite;
    color: #ff0033;
    font-size: 25px;
}
@keyframes heartbeat {
    0% { transform: scale(1); }
    25% { transform: scale(1.3); }
    50% { transform: scale(1); }
    75% { transform: scale(1.3); }
    100% { transform: scale(1); }
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>🏥 Real-Time Newborn ICU Monitor</h1>", unsafe_allow_html=True)
st.markdown('<p class="pulse">❤️</p>', unsafe_allow_html=True)

# -------------------------------
# Patient Management
# -------------------------------
st.sidebar.header("Patient Management")
st.sidebar.header("User Login")
login_email = st.sidebar.text_input("Email")
login_name = st.sidebar.text_input("Name")
if st.sidebar.button("Login"):
    try:
        main.c.execute(
            "INSERT INTO users (email, name) VALUES (?, ?)",
            (login_email, login_name)
        )
        main.conn.commit()
        st.success(f"Logged in as {login_email}")
        st.session_state.user_email = login_email
    except:
        st.warning("Email already registered. Logged in.")
        st.session_state.user_email = login_email

# Add new patient
with st.sidebar.expander("Add New Patient"):
    name = st.text_input("Patient Name")
    age = st.number_input("Age (months)", 0, 120, 1)
    patient_id_input = st.text_input("Patient ID")
    if st.button("Add Patient"):
        try:
            main.c.execute(
                'INSERT INTO patients (name, age, patient_id) VALUES (?, ?, ?)',
                (name, age, patient_id_input)
            )
            main.conn.commit()
            st.success(f"Patient {name} added successfully!")
        except:
            st.error("Patient ID must be unique.")

# Select patient
st.sidebar.header("Select Patient")
patients = pd.read_sql_query("SELECT * FROM patients", main.conn)
patient_options = patients["patient_id"].tolist()
selected_patient = st.sidebar.selectbox("Patient ID", [""] + patient_options)

if selected_patient == "":
    st.warning("Please select a patient to start monitoring.")
    st.stop()

# -------------------------------
# Initialize session state
# -------------------------------
if "run_monitor" not in st.session_state:
    st.session_state.run_monitor = False

if "stop_monitor" not in st.session_state:
    st.session_state.stop_monitor = False

if "prev_status" not in st.session_state:
    st.session_state.prev_status = "✅ Safe"

# -------------------------------
# Hidden audio playback
# -------------------------------
def play_audio_hidden(audio_file_path):
    with open(audio_file_path, "rb") as f:
        audio_bytes = f.read()
        b64 = base64.b64encode(audio_bytes).decode()
        md = f"""
        <audio autoplay="true" style="display:none;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
        st.markdown(md, unsafe_allow_html=True)

alert_file = "alert.mp3"  # make sure this file exists in repo

# -------------------------------
# Live Monitor Controls
# -------------------------------
col1, col2 = st.columns(2)
with col1:
    if st.button("Start Real-Time Monitor"):
        st.session_state.run_monitor = True
        st.session_state.stop_monitor = False

with col2:
    if st.button("Stop Monitor"):
        st.session_state.run_monitor = False
        st.session_state.stop_monitor = True

# Placeholders for charts and latest reading
chart_placeholder = st.empty()
latest_placeholder = st.empty()

# -------------------------------
# Real-Time Monitoring Loop
# -------------------------------
if st.session_state.run_monitor:
    while st.session_state.run_monitor:
        # Simulate vitals
        heart_rate = np.random.randint(80, 160)
        oxygen_level = np.random.randint(85, 100)
        blood_pressure = np.random.randint(60, 100)

        # Predict status
        high_risk = main.predict_function([heart_rate, oxygen_level, blood_pressure]) == 1
        status = "⚠️ ALERT!" if high_risk else "✅ Safe"

        # Play alert only if status changes to ALERT
        if high_risk and st.session_state.prev_status != "⚠️ ALERT!":
            if os.path.exists(alert_file):
                play_audio_hidden(alert_file)

        st.session_state.prev_status = status

        # Save reading to DB
        main.save_reading(selected_patient, heart_rate, oxygen_level, blood_pressure, status)

        # Fetch last 50 readings
        readings = main.get_last_readings(selected_patient, n=50)

        # Display latest reading
        latest_placeholder.markdown(f'<div class="status-card"><h3>Latest Reading</h3>{readings.iloc[-1].to_dict()}</div>', unsafe_allow_html=True)

        # Display live chart
        chart_data = readings[["heart_rate", "oxygen_level", "blood_pressure"]]
        chart_placeholder.line_chart(chart_data)

        # Realistic pace
        time.sleep(2.5)

# -------------------------------
# Historical Data
# -------------------------------
st.subheader("Patient Historical Data")
historical = pd.read_sql_query(
    f'SELECT * FROM readings WHERE patient_id="{selected_patient}" ORDER BY reading_id DESC',
    main.conn
)
st.dataframe(historical)
st.subheader("Feedback")
feedback_msg = st.text_area("Enter your feedback or suggestions")
if st.button("Submit Feedback"):
    if "user_email" in st.session_state:
        main.c.execute(
            "INSERT INTO feedback (user_email, message) VALUES (?, ?)",
            (st.session_state.user_email, feedback_msg)
        )
        main.conn.commit()
        st.success("Thank you for your feedback!")
    else:
        st.error("Please login first to submit feedback.")
