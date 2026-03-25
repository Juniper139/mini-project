from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
import json

if __name__ == "__main__":
    # Load model
    model = YOLO("runs/detect/human_model_final/weights/best.pt")

    # MQTT setup
    client = mqtt.Client()
    client.connect("localhost", 1883, 60)
    client.loop_start()

    # Image path
    image_path = r"D:\miniproject\miniproject\Humans.v1i.yolov8\test\Screenshot 2025-07-29 232938.png"

    # Run prediction
    results = model.predict(
        source=image_path,
        imgsz=640,
        conf=0.25,
        device=0,
        save=True
    )

    # ✅ Process results PROPERLY
    for result in results:
        boxes = result.boxes

        person_count = len(boxes)
        print (f"Number of people detected: {person_count}")

        data = {"people_count": person_count}
        client.publish("yolo/detection", json.dumps(data))

        # 🖼️ THEN show image
        img = result.plot()
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        plt.imshow(img)
        plt.axis('off')
        plt.show()

       