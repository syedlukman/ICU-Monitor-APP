# main.py
import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

# ------------------------------
# Database setup
# ------------------------------
conn = sqlite3.connect("icu_monitor.db", check_same_thread=False)
c = conn.cursor()

# Create patients table
c.execute("""
CREATE TABLE IF NOT EXISTS patients (
    patient_id TEXT PRIMARY KEY,
    name TEXT,
    age INTEGER
)
""")

# Create readings table
c.execute("""
CREATE TABLE IF NOT EXISTS readings (
    reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT,
    heart_rate INTEGER,
    oxygen_level INTEGER,
    blood_pressure INTEGER,
    status TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# ------------------------------
# Train simple ML model
# ------------------------------
# Simulate ICU data
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

# Save model
joblib.dump(model, "cardiac_model.pkl")

# ------------------------------
# Prediction function
# ------------------------------
def predict_function(vitals):
    """
    vitals: list [heart_rate, oxygen_level, blood_pressure]
    returns: 1 if high-risk, 0 if safe
    """
    return model.predict([vitals])[0]

# ------------------------------
# Save reading
# ------------------------------
def save_reading(patient_id, heart_rate, oxygen_level, blood_pressure, status):
    c.execute(
        "INSERT INTO readings (patient_id, heart_rate, oxygen_level, blood_pressure, status) VALUES (?, ?, ?, ?, ?)",
        (patient_id, heart_rate, oxygen_level, blood_pressure, status)
    )
    conn.commit()

# ------------------------------
# Get last N readings
# ------------------------------
def get_last_readings(patient_id, n=50):
    df = pd.read_sql_query(
        f"SELECT * FROM readings WHERE patient_id='{patient_id}' ORDER BY reading_id DESC LIMIT {n}",
        conn
    )
    return df.iloc[::-1]  # reverse to chronological order
# Users table
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    name TEXT
)
""")

# Feedback table
c.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()
