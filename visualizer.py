# enhanced_visualizer.py
import sys, pygame, random, math, time
from newalgo1 import get_traffic_plan

# ---------- CONFIG ----------
JUNCTION_TYPE = 4           # 3 or 4
TOTAL_CYCLE_TIME = 30.0     # seconds per full cycle (green-only sum; yellow added on top)
MIN_GREEN = 6.0             # min per phase (seconds)
YELLOW_TIME = 2.0           # amber time appended to each phase (seconds)
WINDOW = (1200, 800)
FPS = 60

# Use your files or camera snapshots here
images = {
    "north": "exone.webp",
    "south": "extwo.jpg",
    "east":  "exthree.webp",
    "west":  "exfour.jpg"
}

# ---------- PYGAME INIT ----------
pygame.init()
screen = pygame.display.set_mode(WINDOW)
pygame.display.set_caption("Adaptive Traffic Signal — Enhanced Visualization")
clock = pygame.time.Clock()
font_xs = pygame.font.SysFont(None, 16)
font_sm = pygame.font.SysFont(None, 20)
font_md = pygame.font.SysFont(None, 28)
font_lg = pygame.font.SysFont(None, 36)
font_xl = pygame.font.SysFont(None, 48)

# ---------- COLORS ----------
BG = (25, 25, 30)
ROAD = (70, 70, 75)
ROAD_MARKING = (200, 200, 200)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 100)
YELLOW = (255, 200, 0)
BLUE = (60, 120, 255)
GRAY = (130, 130, 130)
DARK_GRAY = (60, 60, 65)
LIGHT_GRAY = (180, 180, 185)

# Car colors
CAR_COLORS = [
    (220, 20, 60),   # Crimson
    (30, 144, 255),  # Dodger Blue
    (255, 140, 0),   # Dark Orange
    (50, 205, 50),   # Lime Green
    (218, 112, 214), # Orchid
    (255, 215, 0),   # Gold
    (128, 0, 128),   # Purple
    (255, 69, 0),    # Orange Red
]

# ---------- ENHANCED GEOMETRY ----------
W, H = WINDOW
CX, CY = W // 2, H // 2
LANE = 100          # each road thickness
LANE_WIDTH = 40     # single lane width
STOP_DIST = 80      # stop line offset from center
CAR_W, CAR_H = 24, 42
GAP = 20            # min gap between queued cars
LIGHT_RADIUS = 18
LIGHT_BORDER = 3

# Enhanced stop lines
STOP_LINES = {
    "north": pygame.Rect(CX - LANE//2 + 5, CY - STOP_DIST - 3, LANE - 10, 6),
    "south": pygame.Rect(CX - LANE//2 + 5, CY + STOP_DIST - 3, LANE - 10, 6),
    "east":  pygame.Rect(CX + STOP_DIST - 3, CY - LANE//2 + 5, 6, LANE - 10),
    "west":  pygame.Rect(CX - STOP_DIST - 3, CY - LANE//2 + 5, 6, LANE - 10),
}

# Enhanced signal positions
LIGHT_POS = {
    "north": (CX - 40, CY - STOP_DIST - 40),
    "south": (CX + 40, CY + STOP_DIST + 40),
    "east":  (CX + STOP_DIST + 40, CY - 40),
    "west":  (CX - STOP_DIST - 40, CY + 40),
}

# Enhanced spawn and movement
SPAWN = {
    "north": (CX - LANE_WIDTH//2, H + 80),
    "south": (CX + LANE_WIDTH//2, -80),
    "east":  (-80, CY - LANE_WIDTH//2),
    "west":  (W + 80, CY + LANE_WIDTH//2),
}

VEL = {
    "north": (0, -2.5),
    "south": (0,  2.5),
    "east":  ( 2.8, 0),
    "west":  (-2.8, 0),
}

# ---------- ENHANCED VEHICLES ----------
class Car:
    __slots__ = ("x", "y", "dir", "color", "waiting", "speed", "max_speed", "acceleration", "deceleration", "id")
    
    def __init__(self, road, color=None):
        self.dir = road
        self.x, self.y = SPAWN[road]
        self.color = color or random.choice(CAR_COLORS)
        self.waiting = True
        self.speed = 0.0
        self.max_speed = 2.5 + random.uniform(-0.3, 0.3)  # slight variation
        self.acceleration = 0.08
        self.deceleration = 0.12
        self.id = random.randint(1000, 9999)

    @property
    def rect(self):
        if self.dir in ("north", "south"):
            return pygame.Rect(int(self.x - CAR_W/2), int(self.y - CAR_H/2), CAR_W, CAR_H)
        else:
            return pygame.Rect(int(self.x - CAR_H/2), int(self.y - CAR_W/2), CAR_H, CAR_W)

    def advance(self, can_move=True):
        """Improved movement with proper physics and stopping behavior"""
        target_speed = self.max_speed if can_move and not self.waiting else 0.0
        
        # Smooth acceleration/deceleration
        if self.speed < target_speed:
            self.speed = min(target_speed, self.speed + self.acceleration)
        elif self.speed > target_speed:
            self.speed = max(target_speed, self.speed - self.deceleration)
        
        # Apply movement based on current speed
        if self.dir == "north":
            self.y -= self.speed
        elif self.dir == "south":
            self.y += self.speed
        elif self.dir == "east":
            self.x += self.speed
        elif self.dir == "west":
            self.x -= self.speed

    def past_center(self):
        """Check if car has cleared the intersection properly"""
        clearance = 150
        if self.dir == "north": return self.y < CY - clearance
        if self.dir == "south": return self.y > CY + clearance
        if self.dir == "east":  return self.x > CX + clearance
        if self.dir == "west":  return self.x < CX - clearance
        return False

# Statistics tracking
class Stats:
    def __init__(self):
        self.cars_passed = {road: 0 for road in ["north", "south", "east", "west"]}
        self.total_wait_time = 0
        self.cars_spawned = 0
        self.start_time = time.time()
    
    def car_passed(self, road):
        self.cars_passed[road] += 1
    
    def get_throughput(self):
        elapsed = time.time() - self.start_time
        total_passed = sum(self.cars_passed.values())
        return total_passed / max(1, elapsed / 60)  # cars per minute

# Global statistics
stats = Stats()
queues = {r: [] for r in ["north", "south", "east", "west"]}

def spawn_initial(counts_by_road):
    """Initialize queues with cars properly lined up behind stop lines"""
    for road, det in counts_by_road.items():
        total = sum(det.get(k,0) for k in det) if isinstance(det, dict) else int(det)
        total = max(0, min(12, total))
        
        for i in range(total):
            car = Car(road)
            # Position cars in queue behind stop line, with proper spacing
            queue_spacing = (CAR_H + GAP) * (i + 1)  # +1 to start behind stop line
            
            if road == "north":
                # Cars queue upward (higher Y values) from stop line
                car.y = STOP_LINES[road].bottom + CAR_H/2 + 15 + queue_spacing
            elif road == "south":
                # Cars queue downward (lower Y values) from stop line  
                car.y = STOP_LINES[road].top - CAR_H/2 - 15 - queue_spacing
            elif road == "east":
                # Cars queue leftward (lower X values) from stop line
                car.x = STOP_LINES[road].left - CAR_H/2 - 15 - queue_spacing
            else:  # west
                # Cars queue rightward (higher X values) from stop line
                car.x = STOP_LINES[road].right + CAR_H/2 + 15 + queue_spacing
            
            car.waiting = True  # All cars start waiting
            car.speed = 0.0     # All cars start stationary
            queues[road].append(car)
            stats.cars_spawned += 1

def spawn_periodic(dt, base_spawn_rate):
    """Enhanced periodic spawning with traffic waves"""
    for road, per_min in base_spawn_rate.items():
        # Add some randomness to create traffic waves
        wave_factor = 1 + 0.3 * math.sin(time.time() * 0.5 + hash(road) % 100)
        adjusted_rate = per_min * wave_factor
        
        p = (adjusted_rate / 60.0) * dt
        if random.random() < p:
            queues[road].append(Car(road))
            stats.cars_spawned += 1

def update_queues_enhanced(current_green_roads, green_active):
    """Enhanced queue update with proper traffic flow logic"""
    for road, q in queues.items():
        if not q:
            continue
            
        can_go = (road in current_green_roads) and green_active
        sl = STOP_LINES[road]
        
        # Process cars from front to back (lead car first)
        for i, car in enumerate(q):
            # Calculate stop position and distances properly
            if road == "north":
                stop_pos = sl.bottom + CAR_H/2 + 15
                dist_to_stop = car.y - stop_pos
                approaching_stop = dist_to_stop > 0
                at_stop_line = abs(dist_to_stop) <= 5
            elif road == "south":
                stop_pos = sl.top - CAR_H/2 - 15
                dist_to_stop = stop_pos - car.y
                approaching_stop = dist_to_stop > 0
                at_stop_line = abs(dist_to_stop) <= 5
            elif road == "east":
                stop_pos = sl.left - CAR_H/2 - 15
                dist_to_stop = stop_pos - car.x
                approaching_stop = dist_to_stop > 0
                at_stop_line = abs(dist_to_stop) <= 5
            else:  # west
                stop_pos = sl.right + CAR_H/2 + 15
                dist_to_stop = car.x - stop_pos
                approaching_stop = dist_to_stop > 0
                at_stop_line = abs(dist_to_stop) <= 5

            # Check if blocked by car ahead
            blocked_by_car_ahead = False
            safe_distance = CAR_H + GAP + (car.speed * 8)  # Dynamic following distance
            
            if i > 0:  # Not the lead car
                prev_car = q[i-1]
                if road == "north":
                    following_distance = prev_car.y - car.y
                elif road == "south":
                    following_distance = car.y - prev_car.y
                elif road == "east":
                    following_distance = car.x - prev_car.x
                else:  # west
                    following_distance = prev_car.x - car.x
                
                blocked_by_car_ahead = following_distance <= safe_distance

            # Enhanced decision logic
            if i == 0:  # Lead car
                if approaching_stop and not can_go:
                    # Red light ahead - should we stop?
                    stopping_distance = (car.speed * car.speed) / (2 * car.deceleration * 60) + CAR_H
                    
                    if dist_to_stop <= stopping_distance + 20:
                        # Too close to stop safely or already at stop line
                        if at_stop_line:
                            car.waiting = True  # Must stop at line
                        else:
                            car.waiting = False  # Continue through (too late to stop)
                    else:
                        car.waiting = True  # Can stop safely
                elif at_stop_line and not can_go:
                    car.waiting = True  # Must wait at red light
                else:
                    car.waiting = False  # Green light or past stop line
                    
            else:  # Following car
                if blocked_by_car_ahead:
                    car.waiting = True
                elif approaching_stop and not can_go and not blocked_by_car_ahead:
                    # Check if we should stop for red light
                    stopping_distance = (car.speed * car.speed) / (2 * car.deceleration * 60) + CAR_H
                    if dist_to_stop <= stopping_distance + 20 and dist_to_stop > 10:
                        car.waiting = True
                    else:
                        car.waiting = False
                else:
                    car.waiting = False

            # Move the car with improved physics
            car.advance(not blocked_by_car_ahead)

    # Remove cars that have passed through and update stats
    for road in list(queues.keys()):
        cars_to_remove = []
        for car in queues[road]:
            if car.past_center():
                cars_to_remove.append(car)
                stats.cars_passed[road] += 1
        
        for car in cars_to_remove:
            queues[road].remove(car)

def draw_enhanced_scene(green_roads, phase_time_left, is_yellow, phases, phase_idx):
    """Enhanced drawing with better graphics and more information"""
    screen.fill(BG)

    # Draw road base
    pygame.draw.rect(screen, ROAD, (CX - LANE//2, 0, LANE, H))
    pygame.draw.rect(screen, ROAD, (0, CY - LANE//2, W, LANE))
    
    # Road markings - lane dividers
    for i in range(0, H, 40):
        pygame.draw.rect(screen, ROAD_MARKING, (CX - 2, i, 4, 20))
    for i in range(0, W, 40):
        pygame.draw.rect(screen, ROAD_MARKING, (i, CY - 2, 20, 4))

    # Draw intersection area
    pygame.draw.rect(screen, DARK_GRAY, (CX - LANE//2, CY - LANE//2, LANE, LANE))

    # Enhanced stop lines with better visibility
    for road, rect in STOP_LINES.items():
        pygame.draw.rect(screen, WHITE, rect)
        # Add dashed extension
        if road in ("north", "south"):
            for x in range(rect.left - 30, rect.right + 30, 10):
                if x < rect.left or x > rect.right:
                    pygame.draw.rect(screen, LIGHT_GRAY, (x, rect.y, 5, rect.height))
        else:
            for y in range(rect.top - 30, rect.bottom + 30, 10):
                if y < rect.top or y > rect.bottom:
                    pygame.draw.rect(screen, LIGHT_GRAY, (rect.x, y, rect.width, 5))

    # Enhanced traffic lights with housing
    for road, pos in LIGHT_POS.items():
        # Light housing
        housing_rect = pygame.Rect(pos[0] - LIGHT_RADIUS - 8, pos[1] - LIGHT_RADIUS - 8, 
                                 (LIGHT_RADIUS + 8) * 2, (LIGHT_RADIUS + 8) * 2)
        pygame.draw.rect(screen, (40, 40, 45), housing_rect, border_radius=8)
        pygame.draw.rect(screen, (80, 80, 85), housing_rect, 3, border_radius=8)
        
        # Determine light color
        if road in green_roads and not is_yellow:
            color = GREEN
            glow_color = (0, 255, 0, 30)
        elif road in green_roads and is_yellow:
            color = YELLOW
            glow_color = (255, 255, 0, 30)
        else:
            color = RED
            glow_color = (255, 0, 0, 30)
        
        # Glow effect
        for r in range(LIGHT_RADIUS + 15, LIGHT_RADIUS - 1, -3):
            alpha = max(0, 40 - (r - LIGHT_RADIUS) * 3)
            glow_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            glow_surf.fill((*color[:3], alpha))
            screen.blit(glow_surf, (pos[0] - r, pos[1] - r), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Main light
        pygame.draw.circle(screen, color, pos, LIGHT_RADIUS)
        pygame.draw.circle(screen, WHITE, pos, LIGHT_RADIUS, 2)
        
        # Countdown timer on active lights
        if road in green_roads:
            countdown_text = str(int(max(0, phase_time_left)))
            text_surf = font_md.render(countdown_text, True, (0, 0, 0))
            text_rect = text_surf.get_rect(center=pos)
            screen.blit(text_surf, text_rect)

    # Enhanced cars with direction indicators and shadows
    for road, q in queues.items():
        for car in q:
            # Car shadow
            shadow_rect = car.rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2
            pygame.draw.rect(screen, (0, 0, 0, 50), shadow_rect, border_radius=6)
            
            # Main car body
            pygame.draw.rect(screen, car.color, car.rect, border_radius=6)
            pygame.draw.rect(screen, WHITE, car.rect, 2, border_radius=6)
            
            # Direction indicator (arrow)
            arrow_color = WHITE
            center_x, center_y = car.rect.center
            
            if road == "north":
                points = [(center_x, center_y - 8), (center_x - 4, center_y - 2), (center_x + 4, center_y - 2)]
            elif road == "south":
                points = [(center_x, center_y + 8), (center_x - 4, center_y + 2), (center_x + 4, center_y + 2)]
            elif road == "east":
                points = [(center_x + 8, center_y), (center_x + 2, center_y - 4), (center_x + 2, center_y + 4)]
            else:  # west
                points = [(center_x - 8, center_y), (center_x - 2, center_y - 4), (center_x - 2, center_y + 4)]
            
            pygame.draw.polygon(screen, arrow_color, points)
            
            # Waiting indicator
            if car.waiting:
                pygame.draw.circle(screen, RED, (center_x, center_y - 15), 3)

    # Enhanced HUD with multiple panels
    draw_hud(green_roads, phase_time_left, is_yellow, phases, phase_idx)
    
    pygame.display.flip()

def draw_hud(green_roads, phase_time_left, is_yellow, phases, phase_idx):
    """Draw comprehensive heads-up display"""
    # Main status panel
    panel_rect = pygame.Rect(10, 10, 400, 120)
    pygame.draw.rect(screen, (0, 0, 0, 150), panel_rect, border_radius=10)
    pygame.draw.rect(screen, WHITE, panel_rect, 2, border_radius=10)
    
    # Phase information
    state_text = "YELLOW" if is_yellow else "GREEN"
    state_color = YELLOW if is_yellow else GREEN
    
    phase_text = font_lg.render(f"Phase {phase_idx + 1}/{len(phases)}: {', '.join(green_roads)}", True, WHITE)
    screen.blit(phase_text, (20, 20))
    
    state_label = font_md.render(f"State: {state_text}", True, state_color)
    screen.blit(state_label, (20, 50))
    
    timer_text = font_md.render(f"Time remaining: {phase_time_left:.1f}s", True, WHITE)
    screen.blit(timer_text, (20, 75))
    
    # Queue status panel
    queue_panel = pygame.Rect(10, 140, 400, 140)
    pygame.draw.rect(screen, (0, 0, 0, 150), queue_panel, border_radius=10)
    pygame.draw.rect(screen, WHITE, queue_panel, 2, border_radius=10)
    
    queue_title = font_md.render("Queue Status", True, WHITE)
    screen.blit(queue_title, (20, 150))
    
    y_offset = 175
    for i, road in enumerate(["north", "south", "east", "west"]):
        queue_size = len(queues[road])
        waiting_cars = sum(1 for car in queues[road] if car.waiting)
        
        color = GREEN if road in green_roads and not is_yellow else RED
        status_text = font_sm.render(f"{road.title()}: {queue_size} cars ({waiting_cars} waiting)", True, color)
        screen.blit(status_text, (20, y_offset + i * 22))

    # Statistics panel
    stats_panel = pygame.Rect(W - 350, 10, 340, 180)
    pygame.draw.rect(screen, (0, 0, 0, 150), stats_panel, border_radius=10)
    pygame.draw.rect(screen, WHITE, stats_panel, 2, border_radius=10)
    
    stats_title = font_md.render("Traffic Statistics", True, WHITE)
    screen.blit(stats_title, (W - 340, 20))
    
    # Throughput
    throughput = stats.get_throughput()
    throughput_text = font_sm.render(f"Throughput: {throughput:.1f} cars/min", True, WHITE)
    screen.blit(throughput_text, (W - 340, 50))
    
    # Cars passed by direction
    total_passed = sum(stats.cars_passed.values())
    total_text = font_sm.render(f"Total cars passed: {total_passed}", True, WHITE)
    screen.blit(total_text, (W - 340, 75))
    
    y_offset = 100
    for road in ["north", "south", "east", "west"]:
        passed = stats.cars_passed[road]
        passed_text = font_xs.render(f"{road.title()}: {passed}", True, WHITE)
        screen.blit(passed_text, (W - 340, y_offset))
        y_offset += 18

    # Next phase preview
    next_panel = pygame.Rect(10, 290, 400, 80)
    pygame.draw.rect(screen, (0, 0, 0, 150), next_panel, border_radius=10)
    pygame.draw.rect(screen, WHITE, next_panel, 2, border_radius=10)
    
    next_title = font_md.render("Next Phase", True, WHITE)
    screen.blit(next_title, (20, 300))
    
    next_phase_idx = (phase_idx + 1) % len(phases)
    next_roads = phases[next_phase_idx]
    next_text = font_sm.render(f"Phase {next_phase_idx + 1}: {', '.join(next_roads)}", True, GRAY)
    screen.blit(next_text, (20, 330))

def draw_loading_screen():
    """Draw loading screen while initializing"""
    screen.fill(BG)
    loading_text = font_xl.render("Initializing Traffic System...", True, WHITE)
    loading_rect = loading_text.get_rect(center=(W//2, H//2))
    screen.blit(loading_text, loading_rect)
    
    # Animated loading bar
    bar_width = 300
    bar_height = 10
    bar_rect = pygame.Rect(W//2 - bar_width//2, H//2 + 50, bar_width, bar_height)
    pygame.draw.rect(screen, GRAY, bar_rect, border_radius=5)
    
    # Animated progress
    progress = (time.time() * 2) % 1
    progress_width = int(bar_width * progress)
    progress_rect = pygame.Rect(bar_rect.x, bar_rect.y, progress_width, bar_height)
    pygame.draw.rect(screen, BLUE, progress_rect, border_radius=5)
    
    pygame.display.flip()

def main():
    """Enhanced main loop with better error handling and features"""
    # Show loading screen
    draw_loading_screen()
    
    try:
        # Get traffic plan from detections
        phases, green_times, counts_by_road, _scores = get_traffic_plan(
            images, junction_type=JUNCTION_TYPE, total_cycle_time=TOTAL_CYCLE_TIME, min_green=MIN_GREEN
        )
    except Exception as e:
        print(f"Error getting traffic plan: {e}")
        # Fallback to default phases
        if JUNCTION_TYPE == 4:
            phases = [["north", "south"], ["east", "west"]]
            green_times = [15.0, 15.0]
        else:
            phases = [["north"], ["east"], ["south"]]
            green_times = [10.0, 10.0, 10.0]
        counts_by_road = {"north": 5, "south": 5, "east": 5, "west": 5}

    # Initialize
    spawn_initial(counts_by_road)

    # Enhanced spawn rates with traffic patterns
    base_spawn_rate = {}
    for road in ["north", "south", "east", "west"]:
        total = 0
        if road in counts_by_road:
            v = counts_by_road[road]
            total = sum(v.values()) if isinstance(v, dict) else int(v)
        # More realistic spawn rates
        base_spawn_rate[road] = max(8, min(25, total * 4))

    phase_idx = 0
    state = "GREEN"
    timer = green_times[phase_idx]
    
    # Performance tracking
    frame_count = 0
    fps_update_timer = 0

    running = True
    paused = False
    
    while running:
        dt = clock.tick(FPS) / 1000.0
        fps_update_timer += dt
        frame_count += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    # Reset simulation
                    for q in queues.values():
                        q.clear()
                    spawn_initial(counts_by_road)
                    stats.__init__()
                elif event.key == pygame.K_n:
                    # Skip to next phase
                    if state == "GREEN":
                        state = "YELLOW"
                        timer = YELLOW_TIME
                    else:
                        phase_idx = (phase_idx + 1) % len(phases)
                        state = "GREEN"
                        timer = green_times[phase_idx]

        if not paused:
            current_roads = phases[phase_idx]

            # Update spawns
            spawn_periodic(dt, base_spawn_rate)

            # Update queue dynamics
            green_active = (state == "GREEN")
            update_queues_enhanced(current_roads, green_active)

            # Phase timing
            timer -= dt
            if timer <= 0:
                if state == "GREEN":
                    state = "YELLOW"
                    timer = YELLOW_TIME
                else:
                    phase_idx = (phase_idx + 1) % len(phases)
                    state = "GREEN"
                    timer = green_times[phase_idx]

        # Draw everything
        draw_enhanced_scene(current_roads, timer, is_yellow=(state == "YELLOW"), phases=phases, phase_idx=phase_idx)
        
        # Draw pause indicator
        if paused:
            pause_surf = font_lg.render("PAUSED - Press SPACE to resume", True, YELLOW)
            pause_rect = pause_surf.get_rect(center=(W//2, 50))
            pygame.draw.rect(screen, (0, 0, 0, 150), pause_rect.inflate(20, 10), border_radius=10)
            screen.blit(pause_surf, pause_rect)
        
        # Controls help
        help_texts = [
            "SPACE: Pause/Resume",
            "R: Reset simulation", 
            "N: Next phase",
            "ESC: Exit"
        ]
        for i, text in enumerate(help_texts):
            help_surf = font_xs.render(text, True, LIGHT_GRAY)
            screen.blit(help_surf, (W - 150, H - 80 + i * 16))
        
        # FPS counter
        if fps_update_timer >= 1.0:
            current_fps = frame_count / fps_update_timer
            fps_text = font_xs.render(f"FPS: {current_fps:.1f}", True, WHITE)
            screen.blit(fps_text, (W - 80, 10))
            frame_count = 0
            fps_update_timer = 0

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()