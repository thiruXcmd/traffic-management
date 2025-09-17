# 🚦 Adaptive Traffic Signal Management with Visualization

This project demonstrates an **AI-powered adaptive traffic management system** that uses **vehicle detection** and **dynamic signal allocation** to optimize traffic flow at junctions. It also includes a **pygame-based visualization** to simulate real-world signal behavior and vehicle movement.

##  Features
- **Vehicle Detection** using [Ultralytics RT-DETR](https://docs.ultralytics.com/) (cars, buses, trucks).
- **Dynamic Signal Timing** allocation based on weighted traffic load.
- **Supports 3-way and 4-way junctions** with customizable phases.
- **Realistic Visualization** in `pygame`:
  - Cars spawn and queue behind stop lines.
  - Smooth acceleration/deceleration.
  - Traffic lights with countdown timers, glow effects, and HUD.
  - Live throughput and queue statistics.
- **Fallback Dummy Mode** (random vehicle counts) if object detection is unavailable.

##  Project Structure
├── newalgo.py # Basic traffic algorithm with RT-DETR
├── newalgo1.py # Enhanced algorithm with dummy fallback & scoring
├── object detection.py # Standalone vehicle detection + visualization
├── visualizer.py # Pygame-based traffic signal simulation
└── README.md # Project documentation
Usage
1. Vehicle Detection Test
python "object detection.py"

Detects cars, buses, trucks in an image (cars1.webp by default).
Saves annotated output as output.jpg.

Run Adaptive Traffic Simulation
python visualizer.py

SPACE → Pause/Resume
R → Reset simulation
N → Skip to next phase
ESC → Exit


🛠 Future Improvements
Real-time video stream integration (CCTV feeds).
Multi-lane detection with turning signals.
Data logging for long-term analytics.
Web dashboard (Flask/React + charts).

Developed by Thiru

## Requirements
Install dependencies before running:
```bash
pip install ultralytics pygame matplotlib
Note: RT-DETR model (rtdetr-l.pt) will be automatically downloaded by Ultralytics on first run.

