import spidev
import time
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.animation as animation

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000

WINDOW_SIZE = 400
GRAPH_POINTS = 60
BASELINE_DURATION = 30

def read_adc(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((adc[1] & 3) << 8) + adc[2]

def calculate_bpm(values):
    if len(values) < 100:
        return None

    recent = list(values)[-100:]
    if sum(recent) / len(recent) < 212:
        return None

    avg = sum(values) // len(values)
    threshold = avg + (max(values) - avg) * 0.2

    peaks = 0
    last_peak = -30
    for i in range(1, len(values)-1):
        if values[i] > threshold:
            if values[i] > values[i-1] and values[i] > values[i+1]:
                if i - last_peak > 40:
                    peaks += 1
                    last_peak = i

    duration = len(values) * 0.02
    bpm = round((peaks / duration) * 60)
    return bpm if 30 <= bpm <= 200 else None

# --- Measure baseline ---
input("Put finger on sensor. Press Enter to start baseline (30 seconds)...")
print("Measuring baseline...")
raw_window = deque(maxlen=WINDOW_SIZE)
start = time.time()
while time.time() - start < BASELINE_DURATION:
    raw_window.append(read_adc(0))
    time.sleep(0.02)
    elapsed = int(time.time() - start)
    print(f"\r{elapsed}/30 seconds...", end="")

baseline = calculate_bpm(list(raw_window))
if baseline is None:
    baseline = 70
print(f"\nBaseline: {baseline} BPM")
threshold_line = baseline * 1.08
print(f"Anxiety threshold: {threshold_line:.0f} BPM\n")

# --- Setup graph ---
fig, ax = plt.subplots(figsize=(10, 5))
fig.patch.set_facecolor('black')
ax.set_facecolor('black')
ax.tick_params(colors='white')
ax.spines['bottom'].set_color('white')
ax.spines['left'].set_color('white')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

bpm_history = deque([None] * GRAPH_POINTS, maxlen=GRAPH_POINTS)
line, = ax.plot([], [], color='cyan', linewidth=2)
ax.axhline(y=baseline, color='red', linewidth=1.5, linestyle='--', label=f'Baseline: {baseline}')
ax.axhline(y=threshold_line, color='yellow', linewidth=1.5, linestyle='--', label=f'Threshold: {threshold_line:.0f}')

ax.set_xlim(0, GRAPH_POINTS)
ax.set_ylim(40, 120)
ax.set_xlabel('Seconds', color='white')
ax.set_ylabel('BPM', color='white')
ax.legend(facecolor='black', labelcolor='white')

bpm_text = ax.text(0.98, 0.95, '', transform=ax.transAxes,
                   fontsize=32, color='cyan', fontweight='bold',
                   ha='right', va='top')

status_text = ax.text(0.5, 0.05, '', transform=ax.transAxes,
                      fontsize=16, ha='center', va='bottom')

last_update = time.time()

def update(frame):
    global last_update

    raw_window.append(read_adc(0))
    time.sleep(0.02)

    if time.time() - last_update >= 1.0:
        bpm = calculate_bpm(list(raw_window))
        bpm_history.append(bpm)

        data = [b for b in bpm_history if b is not None]
        if data:
            xs = [i for i, b in enumerate(bpm_history) if b is not None]
            line.set_data(xs, data)

        if bpm:
            bpm_text.set_text(f"{bpm} BPM")
            if bpm >= threshold_line:
                status_text.set_text("ANXIETY DETECTED")
                status_text.set_color('red')
            else:
                status_text.set_text("Normal")
                status_text.set_color('green')
        else:
            bpm_text.set_text("--")
            status_text.set_text("No finger detected")
            status_text.set_color('gray')

        last_update = time.time()

    return line, bpm_text, status_text

ani = animation.FuncAnimation(fig, update, interval=20, blit=True)
plt.tight_layout()
plt.show()
