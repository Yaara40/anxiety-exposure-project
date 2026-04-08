import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000

def read_adc(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((adc[1] & 3) << 8) + adc[2]

print("שים אצבע יציבה - 10 שניות...")
time.sleep(1)

values = []
timestamps = []
start = time.time()

for i in range(500):
    values.append(read_adc(0))
    timestamps.append(time.time() - start)
    time.sleep(0.02)

# סינון ערכי 0
filtered = [(v, t) for v, t in zip(values, timestamps) if v > 10]
vals = [x[0] for x in filtered]

avg = sum(vals) // len(vals)
threshold = avg + (max(vals) - avg) * 0.2

print(f"סף זיהוי: {threshold:.0f}")

# זיהוי פיקים
peaks = 0
last_peak = -30
for i in range(1, len(vals)-1):
    if vals[i] > threshold:
        if vals[i] > vals[i-1] and vals[i] > vals[i+1]:
            if i - last_peak > 25:
                peaks += 1
                last_peak = i

duration = len(vals) * 0.02
bpm = (peaks / duration) * 60
print(f"פעימות שזוהו: {peaks}")
print(f"BPM: {bpm:.0f}")
