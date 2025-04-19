# 🛡️ Real-Time Violence Detection System using YOLO & Pushbullet

This is a Flask-based real-time **Violence Detection System** that uses a trained YOLO model to detect violent activities from camera streams and sends **instant alerts** using Pushbullet.

## 🚨 Features

- 🎥 Real-time detection from multiple cameras (Camera1, Camera2, Camera3)
- 🔎 Uses YOLO (`best.pt`) and optionally `model.h5` for detection
- 🔔 Sends alert notifications using Pushbullet API
- 📊 Displays activity detection only for selected camera
- 💻 Flask Web Interface for interaction
- 🛠️ Easy to set up and customize

---

## 💡 How It Works

1. Select a camera (from 3 options).
2. The video feed is analyzed frame-by-frame.
3. YOLO model detects violent activities.
4. If violence is detected, an **instant Pushbullet notification** is sent.
5. Only the selected camera's feed and activities are displayed on screen.

---

## 🧠 Tech Stack

- **YOLOv5** for object detection (`best.pt`)
- **Python + Flask** for the web backend
- **OpenCV** for camera streaming and processing
- **Pushbullet API** for real-time notifications

---

## 📁 Project Structure
violence-detector/ ├── app.py ├── best.pt ├── model.h5 ├── utils/ │ └── detection_helpers.py ├── templates/ │ └── index.html ├── static/ │ └── style.css ├── requirements.txt └── config.py



---

## 🚀 Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/violence-detector.git
   cd violence-detector

2.Create and activate a virtual environment (recommended)

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
Install dependencies

3.Install dependencies

pip install -r requirements.txt
Add your Pushbullet API key in config.py

4.Add your Pushbullet API key in config.py

PUSHBULLET_API_KEY = "your_access_token_here"
Run the Flask App

5.Run the Flask App

python app.py


📸 Camera Selection
The app supports three camera sources. You can set the camera in the app or code:

if camera == "Camera1":
    cap = cv2.VideoCapture(0)
elif camera == "Camera2":
    cap = cv2.VideoCapture(1)
elif camera == "Camera3":
    cap = cv2.VideoCapture(2)

📬 Pushbullet Notifications
Create a Pushbullet account

Go to Account Settings → Generate Access Token

Replace it in config.py

👩‍💻 Developed By
Rutuja Gaikwad
