import streamlit as st
import pandas as pd
import numpy as np
import time
import base64
import main
import os


st.set_page_config(page_title="Real-Time ICU Monitor", layout="wide")
st.title("🏥 Real-Time Newborn ICU Monitor")


# -------------------------------
# Patient Management
# -------------------------------
st.sidebar.header("Patient Management")


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


# -------------------------------
# Hidden audio playback function
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


# Placeholder for chart and latest reading
chart_placeholder = st.empty()
latest_placeholder = st.empty()


# -------------------------------
# Real-Time Monitoring Loop
# -------------------------------
alert_file = "alert.mp3"  # must exist in repo


if st.session_state.run_monitor:
    while st.session_state.run_monitor:
        # Simulate vital readings
        heart_rate = np.random.randint(80, 160)
        oxygen_level = np.random.randint(85, 100)
        blood_pressure = np.random.randint(60, 100)


        # Predict status
        high_risk = main.predict_function([heart_rate, oxygen_level, blood_pressure]) == 1
        status = "⚠️ ALERT!" if high_risk else "✅ Safe"


        # Play sound if high risk without displaying audio player
        if high_risk and os.path.exists(alert_file):
            play_audio_hidden(alert_file)


        # Save to database
        main.save_reading(selected_patient, heart_rate, oxygen_level, blood_pressure, status)


        # Fetch last 50 readings
        readings = main.get_last_readings(selected_patient, n=50)


        # Display latest reading
        latest_placeholder.subheader("Latest Reading")
        latest_placeholder.write(readings.iloc[-1])


        # Display live chart
        chart_data = readings[["heart_rate", "oxygen_level", "blood_pressure"]]
        chart_placeholder.line_chart(chart_data)


        time.sleep(1)


# -------------------------------
# Historical Data
# -------------------------------
st.subheader("Patient Historical Data")
historical = pd.read_sql_query(
    f'SELECT * FROM readings WHERE patient_id="{selected_patient}" ORDER BY reading_id DESC',
    main.conn
)
st.dataframe(historical)
