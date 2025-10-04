# main.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os
import pygame
import sqlite3
import datetime

# ----------------------------
# Setup Pygame for sound
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
pygame.mixer.init()
alert_sound = os.path.join(BASE_DIR, "alert.mp3")
sound = pygame.mixer.Sound(alert_sound)
channel = pygame.mixer.Channel(0)

# ----------------------------
# Setup database
# ----------------------------
DB_FILE = os.path.join(BASE_DIR, "icu.db")
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
c.execute('''CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                age INTEGER,
                patient_id TEXT UNIQUE
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS readings (
                reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT,
                timestamp TEXT,
                heart_rate INTEGER,
                oxygen_level INTEGER,
                blood_pressure INTEGER,
                status TEXT
            )''')
conn.commit()

# ----------------------------
# Train ML Model
# ----------------------------
data = pd.DataFrame({
    'heart_rate': np.random.randint(80, 160, 1000),
    'oxygen_level': np.random.randint(85, 100, 1000),
    'blood_pressure': np.random.randint(60, 100, 1000),
    'cardiac_arrest': np.random.randint(0, 2, 1000)
})

X = data[['heart_rate', 'oxygen_level', 'blood_pressure']]
y = data['cardiac_arrest']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestClassifier()
model.fit(X_train, y_train)
joblib.dump(model, "cardiac_model.pkl")

# ----------------------------
# Prediction Function
# ----------------------------
def predict_function(baby_input):
    pred = model.predict([baby_input])
    high_risk = pred[0] == 1
    status = "⚠️ ALERT!" if high_risk else "✅ Safe"

    if high_risk and not channel.get_busy():
        channel.play(sound)
    elif not high_risk and channel.get_busy():
        channel.stop()

    return status

# ----------------------------
# Save Reading to Database
# ----------------------------
def save_reading(patient_id, heart_rate, oxygen_level, blood_pressure, status):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''INSERT INTO readings (patient_id, timestamp, heart_rate, oxygen_level, blood_pressure, status)
                 VALUES (?, ?, ?, ?, ?, ?)''', (patient_id, timestamp, heart_rate, oxygen_level, blood_pressure, status))
    conn.commit()

# ----------------------------
# Fetch last N readings for a patient
# ----------------------------
def get_last_readings(patient_id, n=50):
    df = pd.read_sql_query(f'''
        SELECT * FROM readings
        WHERE patient_id = "{patient_id}"
        ORDER BY reading_id DESC
        LIMIT {n}
    ''', conn)
    return df.iloc[::-1]  # reverse to chronological order
