from ultralytics import RTDETR
from collections import Counter

model = RTDETR("rtdetr-l.pt")
VEHICLE_CLASSES = ['car', 'truck', 'bus']
WEIGHTS = {'car': 1.0, 'truck': 3.0, 'bus': 2.5}

def detect_vehicles(image_path):
    results = model(image_path)
    names = results[0].names
    classes = results[0].boxes.cls.cpu().numpy()
    counts = Counter([names[int(cls_id)] for cls_id in classes])
    return {cls: counts.get(cls, 0) for cls in VEHICLE_CLASSES}

def get_vehicle_scores(images):
    scores = {}
    for road, img in images.items():
        counts = detect_vehicles(img)
        scores[road] = sum(WEIGHTS[v] * counts[v] for v in counts)
    return scores

def group_phases(junction_type):
    if junction_type == 4:
        return [
            ['north', 'south'],
            ['east', 'west']
        ]
    elif junction_type == 3:
        return [
            ['north', 'east'],
            ['east', 'south'],
            ['south', 'north']
        ]
    else:
        raise ValueError("Junction must be 3 or 4 roads")

def allocate_phase_times(scores, phases, total_cycle_time=60):
    phase_scores = {i: sum(scores[road] for road in phase) for i, phase in enumerate(phases)}
    total_score = sum(phase_scores.values())
    return {i: round((phase_scores[i] / total_score) * total_cycle_time, 1) for i in phase_scores}

def dynamic_traffic_control(images, junction_type=4, total_cycle_time=60):
    scores = get_vehicle_scores(images)
    phases = group_phases(junction_type)
    phase_times = allocate_phase_times(scores, phases, total_cycle_time)
    
    for i, phase in enumerate(phases):
        print(f"\n PHASE {i+1}: GREEN for {phase_times[i]} sec")
        for road in phase:
            print(f"  {road.upper()} → GREEN")
        for road in images.keys():
            if road not in phase:
                print(f"  {road.upper()} → RED")

# Example usage
images = {
    "north": "exone.webp",
    "south": "extwo.jpg",
    "east": "exthree.webp",
    "west": "exfour.jpg"
}
dynamic_traffic_control(images, junction_type=4)
