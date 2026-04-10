# sensor/bpm_graph.py
import os
import time
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from sensor.bpm_live import read_adc, calculate_bpm, WINDOW_SIZE

os.environ['DISPLAY'] = ':0'
os.environ['QT_QPA_PLATFORM'] = 'xcb'
GRAPH_POINTS = 60

def measure_baseline():
    print("Put finger on sensor. Press Enter to start baseline (30 seconds)...")
    input()
    print("Measuring baseline...")
    raw_window = deque(maxlen=WINDOW_SIZE)
    start = time.time()
    while time.time() - start < 5:#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        raw_window.append(read_adc(0))
        time.sleep(0.02)
        elapsed = int(time.time() - start)
        print(f"\r{elapsed}/30 seconds...", end="")
    baseline = calculate_bpm(list(raw_window))
    if baseline is None:
        baseline = 70
    print(f"\nBaseline: {baseline} BPM\n")
    return baseline

def run_graph(baseline, duration_minutes, on_anxiety_detected):
    threshold_line = baseline * 1.08
    duration_seconds = duration_minutes * 60
    start_time = time.time()

    plt.rcParams['toolbar'] = 'None'
    fig, ax = plt.subplots(figsize=(6.4, 10.24), dpi =100)
    manager = plt.get_current_fig_manager()
    manager.window.showNormal()
    manager.window.setGeometry(640, 0, 640, 1024)

    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    ax.tick_params(colors='white')
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    bpm_history = deque([None] * GRAPH_POINTS, maxlen=GRAPH_POINTS)
    raw_window = deque(maxlen=WINDOW_SIZE)
    line, = ax.plot([], [], color='cyan', linewidth=2)

    ax.plot([0, GRAPH_POINTS], [baseline, baseline],
            color='red', linewidth=1.5, linestyle='--', label=f'Baseline: {baseline}')
    ax.plot([0, GRAPH_POINTS], [threshold_line, threshold_line],
            color='yellow', linewidth=1.5, linestyle='--', label=f'Threshold: {threshold_line:.0f}')

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
    time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes,
                        fontsize=12, color='white', va='top')

    last_update = [time.time()]

    def update(frame):
        elapsed = time.time() - start_time
        remaining = duration_seconds - elapsed
        if remaining <= 0:
            plt.close()
            return line, bpm_text, status_text, time_text

        time_text.set_text(f"Time left: {int(remaining//60):02d}:{int(remaining%60):02d}")
        raw_window.append(read_adc(0))

        if time.time() - last_update[0] >= 1.0:
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
                    on_anxiety_detected()
                else:
                    status_text.set_text("Normal")
                    status_text.set_color('green')
            else:
                bpm_text.set_text("--")
                status_text.set_text("No finger detected")
                status_text.set_color('gray')

            last_update[0] = time.time()

        return line, bpm_text, status_text, time_text

    ani = animation.FuncAnimation(fig, update, interval=20, blit=True, cache_frame_data=False)
    plt.tight_layout()
    plt.show()
