# 🚦 Intelligent Traffic Management System using YOLOv3

An AI-powered Traffic Management System that uses YOLOv3 object detection to analyze traffic density from road images and assist in dynamic traffic signal management.

## 📌 Overview

Traditional traffic signals operate on fixed timers, often causing unnecessary delays and congestion. This project leverages computer vision and deep learning to detect vehicles, estimate traffic density, and support intelligent signal switching based on real-time traffic conditions.

The system processes traffic images, counts vehicles across multiple lanes, and determines which lane should receive priority at the signal.

---

## Preview



https://github.com/user-attachments/assets/368a1f0e-ee75-443a-a025-100d55203302


---


## ✨ Features

- Vehicle detection using YOLOv3
- Traffic density estimation
- Multi-lane traffic analysis
- Dynamic signal switching logic
- Web-based interface for image uploads
- Automatic lane-wise vehicle counting
- Real-time traffic management simulation

---

## 🛠️ Tech Stack

### Backend
- Python
- Flask

### Deep Learning & Computer Vision
- PyTorch
- OpenCV
- YOLOv3

### Frontend
- HTML
- CSS
- JavaScript

---

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/YA-shiKa/traffic-management-system.git
cd traffic-management-system
```

### 2. Create a virtual environment

```bash
python -m venv venv
```
Activate:

Windows
```bash
venv\Scripts\activate
```
Linux/Mac
```bash
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install flask
pip install torch torchvision
pip install opencv-python
pip install numpy
```
### Running the Application

Navigate to the web application folder:
```bash
cd webapp
```

Run:
```bash
python app.py
```
Open your browser and visit:
```bash
http://127.0.0.1:5000
```
Upload traffic images and view the detected vehicles along with lane analysis results.

---

## Working

- User uploads traffic images.
- YOLOv3 detects vehicles in each image.
- Vehicle counts are calculated lane-wise.
- Traffic density is estimated.
- Dynamic signal switching logic identifies the lane with the highest traffic load.
- Results are displayed through the web interface.

---

## Future Enhancements
- Real-time CCTV integration
- Live video stream processing
- Emergency vehicle detection
- Traffic prediction using machine learning
- Smart city integration
- Cloud deployment
