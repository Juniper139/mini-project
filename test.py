from ultralytics import YOLO
import cv2
import paho.mqtt.client as mqtt
import json
import numpy as np
import requests
import time

# ==============================
# CONFIG
# ==============================

ESP32_URL = "http://172.21.40.116/capture"  # your ESP32 IP
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "crowd/data"

# ==============================
# CROWD SETTINGS (EDIT THIS)
# ==============================

AREA = 100                # area size (you decide manually)
WARNING_DENSITY = 0.8
DANGER_DENSITY = 1.5

# ==============================
# LOAD YOLO MODEL
# ==============================

model =YOLO("D:/miniproject/miniproject/runs/detect/human_model_final/weights/best.pt")

# ==============================
# MQTT SETUP
# ==============================

client = mqtt.Client()

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print("MQTT Connected")
except Exception as e:
    print(" MQTT Connection Failed:", e)

print(" Starting detection...")

# ==============================
# MAIN LOOP
# ==============================

while True:
    try:
        # 🔹 Get image from ESP32-CAM
        response = requests.get(ESP32_URL, timeout=5)

        if response.status_code != 200:
            print(" Failed to fetch image")
            continue

        img_arr = np.frombuffer(response.content, np.uint8)
        frame = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)

        if frame is None:
            print(" Invalid frame")
            continue

        # 🔹 Run YOLO
        results = model(frame, imgsz=640, conf=0.25)

        result = results[0]
        boxes = result.boxes

        # 🔹 Count people (class 0 = person)
        person_count = 0
        if boxes is not None:
            for box in boxes:
                if int(box.cls[0]) == 0:
                    person_count += 1

        # 🔹 Calculate density
        density = person_count / AREA if AREA > 0 else 0

        # 🔹 Decide status
        if density > DANGER_DENSITY:
            status = "DANGER"
        elif density > WARNING_DENSITY:
            status = "WARNING"
        else:
            status = "SAFE"

        # 🔹 Print output
        print(f"People: {person_count} | Density: {density:.2f} | Status: {status}")

        # 🔹 Send data via MQTT
        payload = json.dumps({
            "count": person_count,
            "density": density,
            "status": status
        })

        client.publish(MQTT_TOPIC, payload)

        #  Draw results on frame
        output_frame = result.plot()

        #  Add text overlay
        cv2.putText(output_frame, f"Count: {person_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.putText(output_frame, f"Density: {density:.2f}", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        cv2.putText(output_frame, f"Status: {status}", (10, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 0, 255) if status == "DANGER" else (0, 255, 255), 2)

        #  Show window
        cv2.imshow("YOLO ESP32-CAM", output_frame)

        #  Exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        #  Control speed
        time.sleep(1)

    except Exception as e:
        print(" Error:", e)
        time.sleep(5)

# ==============================
# CLEANUP
# ==============================

cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()
print("Stopped")