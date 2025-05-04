# 🎥 Real-Time Anomaly & Speech-Based Emergency Detection System
## About the Project
This project was developed as part of our final year engineering graduation project. Special thanks to my teammates Jeswin Jaison, Ardra Krishna, and Jeeva C.S. for their invaluable contributions and collaboration throughout the development process.
This is a real-time web application for detecting anomalies in video streams and identifying emergency situations through toxic or abusive speech. The system supports both uploaded video analysis and live webcam monitoring, with automatic alert email generation.

---

## 🚀 Features

- 🔍 **Video-based anomaly detection** using a deep learning model (STAE - Spatiotemporal Autoencoder).
- 🧠 **Toxic speech recognition** using Detoxify containing Roberta(Masked Language Modelling)
- 📷 **Live webcam feed analysis** with anomaly and voice detection.
- 📩 **Automated alert email system** triggered by detected emergencies.
- 🌐 **Modern web interface** built with HTML, CSS, and JavaScript.

---

## 🛠️ Tech Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Flask (Python)
- **ML/DL:** Keras (TensorFlow backend)
- **Voice Recognition:** `speech_recognition`, Google Web Speech API
- **Toxicity Detection:** Detoxify
- **Email Alerts:** smtplib, pandas, contacts.xlsx
- **Model:** 3D CNN + ConvLSTM Autoencoder (`saved_model.keras`)

---

## 📁 Project Structure

```
├── app.py                # Flask backend (API routes, live feed, anomaly detection)
├── train.py              # Model training script using Conv3D and ConvLSTM
├── mail.py               # Email alert module using Gmail SMTP
├── frontend/
│   ├── index.html        # Main UI for video upload and live feed
│   ├── styles.css        # Styling for the webpage
│   ├── script.js         # Handles UI logic and API requests
├── uploads/              # Stores uploaded videos
├── detected_frames/      # Stores frames where anomaly is detected
├── contacts.xlsx         # Excel sheet of names and email addresses
├── saved_model.keras     # Trained model file
├── training.npy          # Preprocessed training dataset
```

## 🧪 Train Your Own Model

To train from scratch using your own normal surveillance videos:
```bash
python train.py
```
This generates `saved_model.keras` and `training.npy`.

---

## 🔐 Note on Security

For production, **never expose your mail/password** directly in `mail.py`. Use environment variables or a secure secret manager.



