from flask import Flask, render_template, request, redirect, url_for, session, Response
import os
import numpy as np
import sqlite3
import time
from werkzeug.utils import secure_filename
from ultralytics import YOLO
from pushbullet import Pushbullet
import cv2

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Pushbullet API Setup
PUSHBULLET_API_KEY = "o.rypTpg1kysEH3rPhvzhijkmOIZdqj4DL"  # Replace with your API Key
pb = Pushbullet(PUSHBULLET_API_KEY)

# Location (change this dynamically if needed)
LOCATION = "Pune"  # Change as per your login location (e.g., Mumbai, Nashik, Nagpur) 

# Function to send Pushbullet notifications (every 10 seconds)
last_sent_time = 0

# Folders
UPLOAD_FOLDER = 'static/uploads/'
RESULT_FOLDER = 'static/results/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

# Load models
violence_model = YOLO(r"C:\Users\Asus Laptop\OneDrive\Desktop\Tecnobijproject\violenceDetector_new2\violenceDetector_new\yolov8n.pt")
knife_model = YOLO(r"C:\Users\Asus Laptop\OneDrive\Desktop\Tecnobijproject\violenceDetector_new2\violenceDetector_new\static\models\knife_best.pt")

print("✅ Violence, Knife, and Person Models Loaded Successfully!")

# Database setup
DATABASE = 'user_data.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        city TEXT NOT NULL
                    )''')
    conn.commit()
    conn.close()

init_db() 

def send_pushbullet_notification(title, message):
    global last_sent_time
    current_time = time.time()
    
    # Send notification only if 10 seconds have passed since last notification
    if current_time - last_sent_time >= 10:
        try:
            pb.push_note(title, message)
            print(f"✅ Notification Sent: {title} - {message}")
            last_sent_time = current_time  # Update last sent time
        except Exception as e:
            print(f"❌ Failed to send notification: {e}")

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        city = request.form['city']
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (name, email, city) VALUES (?, ?, ?)", (name, email, city))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Email already registered!"
        finally:
            conn.close()
        return redirect(url_for('login'))
    return render_template('registration.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT city FROM users WHERE email = ? AND name = ?", (email, name))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['user'] = {'name': name, 'email': email, 'city': user[0]}
            return redirect(url_for('index'))
        else:
            return "Invalid login credentials!"
    return render_template('login.html')

@app.route('/index')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))
    city = session['user']['city']
    file = request.files.get('file')
    if not file:
        return "No file selected!"
    filename = secure_filename(file.filename)
    city_folder = os.path.join(app.config['UPLOAD_FOLDER'], city)
    os.makedirs(city_folder, exist_ok=True)
    input_path = os.path.join(city_folder, filename)
    file.save(input_path)
    session['video_path'] = input_path
    return redirect(url_for('welcome'))

@app.route('/welcome')
def welcome():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('result.html', name=session['user']['name'], city=session['user']['city'])

@app.route('/stream')
def stream():
    if 'user' not in session or 'video_path' not in session:
        return redirect(url_for('login'))
    return Response(process_video_realtime(session['video_path']),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/realtime')
def realtime():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('realtime.html')

@app.route('/realtime_stream')
def realtime_stream():
    return Response(process_video_realtime_webcam(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def process_video_realtime_webcam():
    print("🔹 process_video_realtime_webcam() started")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow for Windows

    if not cap.isOpened():
        print("❌ Failed to access webcam!")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to read frame from webcam!")
            break  

        print("✅ Frame captured!")

        violence_results = violence_model(frame, conf=0.7)  # High confidence to filter out false positives
        knife_results = knife_model(frame, conf=0.6)  

        annotated_frame = frame.copy()

        violence_boxes = violence_results[0].boxes.xyxy if violence_results else []
        knife_boxes = knife_results[0].boxes.xyxy if knife_results else []

        violence_detected = False
        knife_detected = len(knife_boxes) > 0  

        # 🚨 Detect Fighting Only (Not Just Presence of People)
        if len(violence_boxes) >= 2:  
            for i in range(len(violence_boxes)):
                x1, y1, x2, y2 = map(int, violence_boxes[i])
                
                for j in range(i + 1, len(violence_boxes)):  
                    x1_other, y1_other, x2_other, y2_other = map(int, violence_boxes[j])

                    # ✅ Check if two people are CLOSE & INTERACTING (possible fight)
                    if abs(x1 - x1_other) < 80 and abs(y1 - y1_other) < 80:
                        violence_detected = True
                        break

        # 🛑 Show "VIOLENCE DETECTED" only if real fighting is detected
        if violence_detected:
            cv2.rectangle(annotated_frame, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 255), 10)
            cv2.putText(annotated_frame, "VIOLENCE DETECTED", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # 🔪 Proper Knife Detection
        if knife_detected:
            for box in knife_boxes:
                x1, y1, x2, y2 = map(int, box)
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 3)
                cv2.putText(annotated_frame, "KNIFE", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)


        # ✅ If NO Violence (no fighting detected) & NO Knife → Show "NON-VIOLENCE"
        if not violence_detected and not knife_detected:
            cv2.rectangle(annotated_frame, (0, 0), (frame.shape[1], frame.shape[0]), (0, 255, 0), 10)
            cv2.putText(annotated_frame, "NON-VIOLENCE", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
        # 🔔 Send Pushbullet Notifications when detected
        if violence_detected:
            send_pushbullet_notification("🚨 Violence Alert!", "Violence detected in live stream!")
        else:
            send_pushbullet_notification("✅ No Violence", "No violent activity detected.")

        if knife_detected:
            send_pushbullet_notification("🔪 Knife Alert!", "A knife has been detected in live stream!")

        _, buffer = cv2.imencode('.jpg', annotated_frame)
        frame_data = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')

    cap.release()
    print("🔹 process_video_realtime_webcam() ended")


def process_video_realtime(input_path, skip_frames=2):
    cap = cv2.VideoCapture(input_path)
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break  

        if frame_count % skip_frames == 0:
            violence_results = violence_model(frame, conf=0.6)  # Increased confidence
            knife_results = knife_model(frame, conf=0.6)  

            # Debugging print statements
            print(f"🔹 Frame {frame_count}:")
            print(f"Violence Detections: {len(violence_results[0].boxes)}")  
            print(f"Knife Detections: {len(knife_results[0].boxes)}")

            annotated_frame = frame.copy()

            violence_detected = False
            knife_detected = False

            # Detecting violence based on specific actions
            if len(violence_results[0].boxes) > 0:
                # Filter for specific violent actions like punching, kicking, etc.
                for box in violence_results[0].boxes.xyxy:
                    # Example: You can add conditions to check for specific violent actions
                    # Pseudo-code: if action == 'punch' or action == 'kick':
                    # Update logic with your action-based detection
                     violence_detected = True

            # Knife detection (keep as is)
            if len(knife_results[0].boxes) > 0:
                knife_detected = True

            # 🔴 Violence Detected (Only if actual detection)
            if violence_detected:
                cv2.rectangle(annotated_frame, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 255), 20)
                cv2.putText(annotated_frame, "VIOLENCE DETECTED", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # 🔵 Knife Detected (Only if actual detection)
            if knife_detected:
                cv2.rectangle(annotated_frame, (0, 0), (frame.shape[1], frame.shape[0]), (255, 0, 0), 20)
                cv2.putText(annotated_frame, "KNIFE DETECTED", (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

                # Draw bounding boxes around knives
                for box in knife_results[0].boxes.xyxy:
                    x1, y1, x2, y2 = map(int, box)
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 3)
                    cv2.putText(annotated_frame, "Knife", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

            # ✅ If NO Violence & NO Knife → Show "NON-VIOLENCE"
            if not violence_detected and not knife_detected:
                cv2.rectangle(annotated_frame, (0, 0), (frame.shape[1], frame.shape[0]), (0, 255, 0), 20)
                cv2.putText(annotated_frame, "NON-VIOLENCE", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            _, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_data = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')

        frame_count += 1

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def test_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not accessible!")
    else:
        print("✅ Camera is working correctly!")

    
    cap.release()

if __name__ == '__main__':
    app.run(debug=False, threaded=True)
