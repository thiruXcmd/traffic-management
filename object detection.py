from ultralytics import RTDETR
from collections import Counter
import matplotlib.pyplot as plt

# Load model
model = RTDETR("rtdetr-l.pt")

# Run inference
results = model("./cars1.webp")

# Save annotated image
results[0].save(filename="output.jpg")

# Get class names for predictions
names = results[0].names
classes = results[0].boxes.cls.cpu().numpy()

# Count specific classes
counts = Counter([names[int(cls_id)] for cls_id in classes])

# Get number of cars and buses
num_cars = counts.get("car", 0)
num_buses = counts.get("bus", 0)
num_truck = counts.get("truck", 0)

print(f"Cars: {num_cars}")
print(f"Buses: {num_buses}")
print(f"truck: {num_truck}")

# Display annotated image
img_with_boxes = results[0].plot()
plt.imshow(img_with_boxes)
plt.axis('off')
plt.show()
