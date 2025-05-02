import os
import cv2
import numpy as np
import imutils
import threading
from flask import Flask, Response, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from keras.models import load_model
import speech_recognition as sr
from detoxify import Detoxify
from mail import send_alert_email

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
DETECTED_FRAMES_FOLDER = os.path.abspath("frontend/detected_frames")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DETECTED_FRAMES_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["DETECTED_FRAMES_FOLDER"] = DETECTED_FRAMES_FOLDER

# Load anomaly detection model
model = load_model("saved_model.keras")
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Function to compute mean squared loss
def mean_squared_loss(x1, x2):
    difference = x1 - x2
    n_samples = np.prod(difference.shape)
    return np.sqrt((difference ** 2).sum()) / n_samples

# Real-time speech detection while analyzing uploaded video
def listen_for_speech_while_processing():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening for speech during video analysis...")
        recognizer.adjust_for_ambient_noise(source)

        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
            detected_text = recognizer.recognize_google(audio)
            print(f"Detected Speech: {detected_text}")

            toxicity_results = Detoxify("unbiased").predict(detected_text)
            print(f"Toxicity Analysis: {toxicity_results}")

            alert_message = check_emergency(toxicity_results)
            if alert_message:
                print(alert_message)
                
                # ✅ Fix: Send alert email safely
                try:
                    send_alert_email("Emergency Alert (During Upload)", alert_message)
                    print("✅ Alert email sent successfully!")
                except Exception as e:
                    print(f"❌ Error sending email: {e}")

        except sr.WaitTimeoutError:
            print("⚠ No speech detected during video processing.")
        except sr.UnknownValueError:
            print("⚠ Could not understand the speech.")
        except sr.RequestError as e:
            print(f"⚠ Speech recognition error: {e}")

# Upload video and analyze anomalies (with real-time speech detection)
@app.route("/upload", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return jsonify({"message": "No file uploaded."}), 400

    file = request.files["video"]
    if file.filename == "":
        return jsonify({"message": "No selected file."}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Start speech detection in a separate thread
    speech_thread = threading.Thread(target=listen_for_speech_while_processing, daemon=True)
    speech_thread.start()

    cap = cv2.VideoCapture(filepath)
    threshold = 0.00054
    frame_skip = 5
    frame_count = 0
    imagedump = []
    anomaly_detected = False
    anomaly_frame_path = os.path.join(DETECTED_FRAMES_FOLDER, "anomaly_frame.jpg")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % frame_skip != 0:
            continue

        frame_resized = cv2.resize(frame, (227, 227))
        gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        gray = (gray - gray.mean()) / gray.std()
        gray = np.clip(gray, 0, 1)
        imagedump.append(gray)

        if len(imagedump) == 10:
            imagedump_np = np.array(imagedump).reshape(227, 227, 10, 1)
            imagedump_np = np.expand_dims(imagedump_np, axis=0)

            output = model.predict(imagedump_np)
            loss = mean_squared_loss(imagedump_np, output)

            if loss > threshold:
                anomaly_detected = True
                cv2.imwrite(anomaly_frame_path, frame)
                break

            imagedump.pop(0)

    cap.release()

    if anomaly_detected:
        return jsonify({"message": "Anomaly Detected!", "frame_url": "/detected_frame"})
    else:
        return jsonify({"message": "No anomaly detected.", "frame_url": None})

# -------------------------
# Live Feed Anomaly Detection + Voice Detection
# -------------------------

output_frame = None
lock = threading.Lock()
live_anomaly_detected = False
camera_active = False

recognizer = sr.Recognizer()

def analyze_text(text):
    results = Detoxify('unbiased').predict(text)
    return results

def check_emergency(results):
    if results["threat"] > 0.2 or results["toxicity"] > 0.6:
        return "⚠ ALERT: Possible emergency detected! Check the environment."
    elif results["identity_attack"] > 0.3 or results["insult"] > 0.4:
        return "⚠ ALERT: Possible harmful or abusive speech detected."
    return None

def listen_and_detect():
    """ Continuously listens for toxic speech when live feed is running. """
    while camera_active:
        with sr.Microphone() as source:
            print("Listening for speech...")
            recognizer.adjust_for_ambient_noise(source)
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = recognizer.recognize_google(audio)
                print(f"Detected Speech: {text}")

                toxicity_results = analyze_text(text)
                print(f"Toxicity Analysis: {toxicity_results}")

                alert_message = check_emergency(toxicity_results)
                if alert_message:
                    print(alert_message)

                    # ✅ Fix: Try sending the email without crashing the thread
                    try:
                        send_alert_email("Emergency Alert", alert_message)
                        print("✅ Alert email sent successfully!")
                    except Exception as e:
                        print(f"❌ Error sending email: {e}")

            except sr.WaitTimeoutError:
                print("⚠ No speech detected, continuing to listen...")
                continue  # ✅ Prevents crash and keeps listening
            
            except sr.UnknownValueError:
                print("⚠ Could not understand the audio, trying again...")
                continue  # ✅ Prevents crash and keeps listening
            
            except sr.RequestError as e:
                print(f"⚠ Speech recognition service error: {e}")
                continue  # ✅ Prevents crash and keeps listening

def detect_live_feed():
    """ Function to analyze live video feed and listen for speech toxicity. """
    global output_frame, live_anomaly_detected, camera_active

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        camera_active = False
        return

    print("Live feed started.")
    camera_active = True
    threshold = 0.00060
    frame_skip = 1
    frame_count = 0
    imagedump = []

    # Start voice detection thread
    voice_thread = threading.Thread(target=listen_and_detect, daemon=True)
    voice_thread.start()

    while camera_active:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame from webcam.")
            break

        frame_count += 1
        if frame_count % frame_skip != 0:
            continue

        frame_resized = cv2.resize(frame, (227, 227))
        gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        gray = (gray - gray.mean()) / gray.std()
        gray = np.clip(gray, 0, 1)
        imagedump.append(gray)

        if len(imagedump) == 10:
            imagedump_np = np.array(imagedump).reshape(227, 227, 10, 1)
            imagedump_np = np.expand_dims(imagedump_np, axis=0)

            output = model.predict(imagedump_np)
            loss = mean_squared_loss(imagedump_np, output)
            print(f"Frame {frame_count}: Loss={loss:.6f}, Threshold={threshold}")

            if loss > threshold:
                live_anomaly_detected = True
                cv2.putText(frame, "Anomaly Detected!", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            else:
                live_anomaly_detected = False

            imagedump.pop(0)

        with lock:
            output_frame = frame.copy()

    cap.release()
    camera_active = False
    print("Webcam feed stopped.")

@app.route("/start_live_feed", methods=["GET"])
def start_live_feed():
    global camera_active
    if camera_active:
        return jsonify({"message": "Live Feed is already running!"})

    print("Starting live feed analysis thread...")
    camera_active = True
    thread = threading.Thread(target=detect_live_feed, daemon=True)
    thread.start()
    return jsonify({"message": "Live Feed Analysis Started!"})

@app.route("/stop_live_feed", methods=["GET"])
def stop_live_feed():
    global camera_active
    if not camera_active:
        return jsonify({"message": "Live Feed is not running!"})

    camera_active = False
    print("Live feed stopped.")
    return jsonify({"message": "Live Feed Stopped!"})

@app.route("/live_feed")
def live_feed():
    def generate_frames():
        global output_frame
        while True:
            with lock:
                if output_frame is None:
                    continue
                _, buffer = cv2.imencode(".jpg", output_frame)
                frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    app.run(debug=True)
