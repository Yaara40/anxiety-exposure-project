import spidev
import time
from collections import deque

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000

WINDOW_SIZE = 500

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

print("Live heart rate monitor - Press Ctrl+C to stop\n")

window = deque(maxlen=WINDOW_SIZE)
last_update = time.time()

try:
    while True:
        window.append(read_adc(0))
        time.sleep(0.02)

        if time.time() - last_update >= 1.0:
            bpm = calculate_bpm(list(window))
            if bpm:
                print(f"BPM: {bpm}")
            last_update = time.time()

except KeyboardInterrupt:
    print("\nStopped.")
