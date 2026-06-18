import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import shutil
from collections import Counter

from flask import Flask, render_template, request, redirect, url_for
import numpy as np
import cv2
import torch
from torch.autograd import Variable
from util.parser import load_classes
from util.model import Darknet
from util.image_processor import preparing_image
from util.utils import non_max_suppression

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

CFG_PATH = os.path.join(ROOT_DIR, "config", "yolov3.cfg")
WEIGHTS_PATH = os.path.join(ROOT_DIR, "weights", "yolov3.weights")
NAMES_PATH = os.path.join(ROOT_DIR, "data", "idd.names")

print("CFG PATH:", CFG_PATH)
print("WEIGHTS PATH:", WEIGHTS_PATH)
print("NAMES PATH:", NAMES_PATH)

BASE_DIR = os.path.dirname(__file__)
STATIC_UPLOADS = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(STATIC_UPLOADS, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = STATIC_UPLOADS

TEST_IMAGE_PATH = "/mnt/data/a2bd4e23-8311-4254-a89d-77d388e05a37.png"

INPUT_RES = 416
CONF_THRESH = 0.3
NMS_THRESH = 0.3

try:
    CLASSES = load_classes(NAMES_PATH)
    print(f"Loaded {len(CLASSES)} class names.")
except Exception as e:
    print("Failed to load class names from", NAMES_PATH, "->", e)
    CLASSES = []

try:
    print("Loading model...", CFG_PATH, WEIGHTS_PATH)
    model = Darknet(CFG_PATH)
    model.load_weights(WEIGHTS_PATH)
    model.hyperparams["height"] = str(INPUT_RES)
    inp_dim = int(model.hyperparams["height"])
    if torch.cuda.is_available():
        model.cuda()
    model.eval()
    print("Model loaded.")
except Exception as e:
    print("Failed to load Darknet model:", e)
    raise


def run_detection_on_image(cv2_img):
    """
    Runs the loaded Darknet YOLO on a single BGR image (numpy).
    Returns: (Counter(classes), vehicle_count)
    """
    if cv2_img is None:
        return Counter(), 0

    try:
        tensor = preparing_image(cv2_img, inp_dim)
    except Exception:
        tensor = preparing_image(cv2_img)
    if not isinstance(tensor, torch.Tensor):
        tensor = torch.from_numpy(tensor).float().div(255.0).unsqueeze(0)

    if torch.cuda.is_available():
        tensor = tensor.cuda()

    with torch.no_grad():
        prediction = model(Variable(tensor))

    prediction = non_max_suppression(prediction, CONF_THRESH, model.num_classes, nms_conf=NMS_THRESH)

    if type(prediction) == int or prediction is None:
        return Counter(), 0

    try:
        out = prediction.cpu().numpy()
    except Exception:
        out = np.array(prediction)

    classes_detected = []
    for row in out:
        try:
            cls_idx = int(row[-1])
            if 0 <= cls_idx < len(CLASSES):
                classes_detected.append(CLASSES[cls_idx])
        except Exception:
            continue

    vc = Counter(classes_detected)
    vehicle_types = {"car", "motorbike", "truck", "bicycle", "autorickshaw", "bus", "van", "bike"}
    vehicle_count = sum(count for cls, count in vc.items() if cls in vehicle_types)

    return vc, vehicle_count

def build_dynamic_sequence(densest_lane, lane_counts):
    """Return structured dynamic signal plan (open, duration, visual steps)."""
    if densest_lane is None:
        return {"active": False}

    base = 20
    extra = int(max(0, lane_counts[densest_lane - 1] - 10) * 2)
    duration = min(135, base + extra)

    seq = {
        "active": True,
        "open_lane": densest_lane,
        "open_message": f"OPENING LANE-{densest_lane}",
        "duration": duration,
        "steps": []
    }

    visual = {
        "row1": ["🔴", "🔴", "🔴", "🔴"],
        "row2": ["⚪", "⚪", "⚪", "⚪"],
        "row3": ["⚪", "⚪", "⚪", "⚪"],
    }
    idx = densest_lane - 1
    visual["row1"][idx] = "⚪"
    visual["row3"][idx] = "🟢"

    seq["steps"].append({
        "title": "Phase: Opening",
        "desc": f"Opening lane {densest_lane} — green for {duration} seconds",
        "visual": visual
    })

    seq["steps"].append({
        "title": "Phase: Counting/Green active",
        "desc": f"LANE-{densest_lane} is OPEN. Counting and traffic flow in progress. Timer will run for {duration} seconds.",
        "visual": visual
    })

    seq["steps"].append({
        "title": "Phase: Closing",
        "desc": f"CLOSING LANE-{densest_lane}. Resetting all to red.",
        "visual": {
            "row1": ["🔴", "🔴", "🔴", "🔴"],
            "row2": ["⚪", "⚪", "⚪", "⚪"],
            "row3": ["⚪", "⚪", "⚪", "⚪"],
        }
    })

    return seq


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_and_detect():
    lane_files = []
    for i in range(1, 5):
        f = request.files.get(f"lane{i}")
        if f and f.filename:
            filename = f"{int(time.time())}_{i}_{secure_filename(f.filename)}"
            savepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            f.save(savepath)
            lane_files.append(savepath)
        else:
            lane_files.append(None)

    summaries = []
    lane_counts = []
    for file in lane_files:
        if file is None:
            summaries.append({"file": None, "vehicle_count": 0, "counts": {}})
            lane_counts.append(0)
            continue
        img = cv2.imread(file)
        counts, total = run_detection_on_image(img)
        filename_only = os.path.basename(file)   # store just the filename (cross-platform)
        summaries.append({"file": filename_only, "vehicle_count": int(total), "counts": dict(counts)})
        lane_counts.append(int(total))


    densest_lane = (int(np.argmax(lane_counts)) + 1) if sum(lane_counts) > 0 else None
    dynamic = build_dynamic_sequence(densest_lane, lane_counts)

    terminal_lines = []
    terminal_lines.append(f"Detected  ({len([f for f in lane_files if f])} inputs)    : \n")
    for i, s in enumerate(summaries, start=1):
        terminal_lines.append(f"Lane : {i} - Number of Vehicles detected :       {s['vehicle_count']}")
        terminal_lines.append("           Vehicle Type    Count")
        if s['counts']:
            for k, v in sorted(s['counts'].items()):
                terminal_lines.append(f"            {k:15s} {v}")
        else:
            terminal_lines.append("            None")
    terminal_lines.append("-" * 120)
    terminal_lines.append(f"🚦 Lane with denser traffic is : Lane {densest_lane if densest_lane is not None else 'N/A'}")
    terminal_text = "\n".join(terminal_lines)

    return render_template(
        "result.html",
        summaries=summaries,
        densest_lane=densest_lane,
        lane_counts=lane_counts,
        dynamic=dynamic,
        terminal=terminal_text
    )

@app.route("/demo", methods=["GET"])
def demo():
    if not os.path.exists(TEST_IMAGE_PATH):
        return f"Demo image not found at {TEST_IMAGE_PATH}. Please upload images manually.", 404

    lane_files = []
    for i in range(1, 5):
        dst_name = f"demo_{int(time.time())}_{i}.png"
        dst_path = os.path.join(app.config["UPLOAD_FOLDER"], dst_name)
        try:
            shutil.copy(TEST_IMAGE_PATH, dst_path)
            lane_files.append(dst_path)
        except Exception:
            lane_files.append(None)

    summaries = []
    lane_counts = []
    for file in lane_files:
        if file is None:
            summaries.append({"file": None, "vehicle_count": 0, "counts": {}})
            lane_counts.append(0)
            continue

        img = cv2.imread(file)
        counts, total = run_detection_on_image(img)

        filename_only = os.path.basename(file)  # ✔ FIXED
        summaries.append({"file": filename_only, "vehicle_count": int(total), "counts": dict(counts)})
        lane_counts.append(int(total))

    densest_lane = (int(np.argmax(lane_counts)) + 1) if sum(lane_counts) > 0 else None
    dynamic = build_dynamic_sequence(densest_lane, lane_counts)

    terminal_lines = []
    terminal_lines.append(f"Detected  ({len([f for f in lane_files if f])} inputs)    : \n")
    for i, s in enumerate(summaries, start=1):
        terminal_lines.append(f"Lane : {i} - Number of Vehicles detected :       {s['vehicle_count']}")
        terminal_lines.append("           Vehicle Type    Count")
        if s['counts']:
            for k, v in sorted(s['counts'].items()):
                terminal_lines.append(f"            {k:15s} {v}")
        else:
            terminal_lines.append("            None")
    terminal_lines.append("-" * 120)
    terminal_lines.append(f"🚦 Lane with densest traffic is : Lane {densest_lane if densest_lane is not None else 'N/A'}")
    terminal_text = "\n".join(terminal_lines)

    return render_template(
        "result.html",
        summaries=summaries,
        densest_lane=densest_lane,
        lane_counts=lane_counts,
        dynamic=dynamic,
        terminal=terminal_text
    )


def secure_filename(filename: str) -> str:
    keepchars = (" ", ".", "_", "-")
    return "".join(c for c in filename if c.isalnum() or c in keepchars).rstrip()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
