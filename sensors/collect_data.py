import spidev
import time
import csv
from datetime import datetime

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000

def read_adc(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((adc[1] & 3) << 8) + adc[2]

def measure_bpm(label, duration_sec=30):
    print(f"Measuring {label}...")
    values = []
    for i in range(duration_sec * 50):
        values.append(read_adc(0))
        time.sleep(0.02)

    filtered = [v for v in values if v > 10]
    if not filtered:
        return None

    avg = sum(filtered) // len(filtered)
    signal_range = max(filtered) - min(filtered)

    # Auto-adjust threshold based on signal quality
    if signal_range < 50:
        multiplier = 0.2
    elif signal_range < 100:
        multiplier = 0.3
    elif signal_range < 200:
        multiplier = 0.35
    else:
        multiplier = 0.4

    threshold = avg + signal_range * multiplier
    print(f"  Signal range: {signal_range} | Multiplier: {multiplier} | Threshold: {threshold:.0f}")

    peaks = 0
    last_peak = -30
    for i in range(1, len(filtered)-1):
        if filtered[i] > threshold:
            if filtered[i] > filtered[i-1] and filtered[i] > filtered[i+1]:
                if i - last_peak > 25:
                    peaks += 1
                    last_peak = i

    return round((peaks / duration_sec) * 60)

# --- Open CSV file ---
filename = f"measurements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
with open(filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['timestamp', 'person', 'measurement_num', 'baseline_bpm', 'stress_bpm', 'diff'])

print(f"Saving to: {filename}")
person_name = input("Enter subject name: ")
measurement_num = 1

while True:
    print(f"\n--- Measurement {measurement_num} ---")
    input("Press Enter to start baseline (30 seconds, stay calm)...")
    baseline = measure_bpm("baseline", 30)
    print(f"Baseline: {baseline} BPM")

    input("Press Enter to start stress phase (play the alarm sound)...")
    stress = measure_bpm("stress", 30)
    print(f"Stress: {stress} BPM")
    print(f"Difference: {stress - baseline:+d} BPM")

    # Save row
    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime('%H:%M:%S'),
            person_name,
            measurement_num,
            baseline,
            stress,
            stress - baseline
        ])

    print("Saved!")
    measurement_num += 1

    cont = input("\nAnother measurement? (y/n): ")
    if cont.lower() != 'y':
        break

print(f"\nDone! Data saved to: {filename}")
