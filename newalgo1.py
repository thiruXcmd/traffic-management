# traffic_algo.py
from collections import Counter
import random

# ---- Try to use Ultralytics RT-DETR; fallback to dummy if not available ----
USE_DUMMY = False
try:
    from ultralytics import RTDETR  # pip install ultralytics
    _model = RTDETR("rtdetr-l.pt")  # downloads on first use
except Exception:
    _model = None
    USE_DUMMY = True

# Vehicles we care about + weights (heavier -> more green time)
VEHICLE_CLASSES = ["car", "truck", "bus"]
WEIGHTS = {"car": 1.0, "truck": 3.0, "bus": 2.5}

def detect_vehicles(image_path):
    """
    Returns a dict like {"car": 3, "truck": 1, "bus": 0}.
    Uses RT-DETR if available, else returns dummy random counts.
    """
    if USE_DUMMY or _model is None:
        return {
            "car": random.randint(0, 6),
            "truck": random.randint(0, 2),
            "bus": random.randint(0, 2),
        }

    results = _model(image_path)
    names = results[0].names
    classes = results[0].boxes.cls.cpu().numpy().tolist() if len(results[0].boxes) else []
    counts = Counter([names[int(cid)] for cid in classes])
    return {cls: int(counts.get(cls, 0)) for cls in VEHICLE_CLASSES}

def get_vehicle_scores(images: dict):
    """
    images: {"north": "path", ...}
    returns:
      counts_by_road: {"north": {"car":2,"truck":1,"bus":0}, ...}
      scores_by_road: {"north": 2*1.0 + 1*3.0 + 0*2.5, ...}
    """
    counts_by_road, scores_by_road = {}, {}
    for road, img in images.items():
        det = detect_vehicles(img)
        counts_by_road[road] = det
        score = sum(WEIGHTS[k] * det.get(k, 0) for k in VEHICLE_CLASSES)
        scores_by_road[road] = score
    return counts_by_road, scores_by_road

def group_phases(junction_type: int):
    """
    Returns list of phases (each phase is a list of roads that are green together).
    """
    if junction_type == 4:
        return [["north", "south"], ["east", "west"]]
    if junction_type == 3:
        # simple T-junction cycle (adjust orientation to your layout)
        return [["north", "east"], ["east", "south"], ["south", "north"]]
    raise ValueError("junction_type must be 3 or 4")

def allocate_phase_times(scores_by_road: dict, phases: list,
                         total_cycle_time: float = 60.0,
                         min_green: float = 6.0):
    """
    Proportional allocation by phase load with a per-phase minimum.
    Returns a list of green durations aligned to `phases`.
    Yellow is handled in the visualizer.
    """
    phase_loads = []
    for phase in phases:
        phase_loads.append(sum(scores_by_road.get(r, 0.0) for r in phase))

    total_load = sum(phase_loads)
    n = len(phases)

    if total_load <= 0:
        # No load detected -> split equally with min_green
        base = max(min_green, total_cycle_time / n)
        return [round(base, 1) for _ in phases]

    # First, give proportional times
    raw_times = [(load / total_load) * total_cycle_time for load in phase_loads]
    # Enforce min green; re-normalize if needed
    times = [max(min_green, t) for t in raw_times]
    factor = total_cycle_time / sum(times)
    times = [round(t * factor, 1) for t in times]
    return times

def get_traffic_plan(images: dict, junction_type: int = 4,
                     total_cycle_time: float = 60.0,
                     min_green: float = 6.0):
    """
    High-level: detect -> score -> phases -> phase green durations.
    Returns: phases(list[list[str]]), green_times(list[float]),
             counts_by_road(dict), scores_by_road(dict)
    """
    counts_by_road, scores_by_road = get_vehicle_scores(images)
    phases = group_phases(junction_type)
    green_times = allocate_phase_times(scores_by_road, phases, total_cycle_time, min_green)
    return phases, green_times, counts_by_road, scores_by_road
