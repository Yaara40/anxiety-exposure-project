import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000

def read_adc(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((adc[1] & 3) << 8) + adc[2]

def measure_bpm(duration_sec=10):
    values = []
    for i in range(duration_sec * 50):
        values.append(read_adc(0))
        time.sleep(0.02)
    
    filtered = [v for v in values if v > 10]
    if not filtered:
        return None
    
    avg = sum(filtered) // len(filtered)
    threshold = avg + (max(filtered) - avg) * 0.2
    
    peaks = 0
    last_peak = -30
    for i in range(1, len(filtered)-1):
        if filtered[i] > threshold:
            if filtered[i] > filtered[i-1] and filtered[i] > filtered[i+1]:
                if i - last_peak > 25:
                    peaks += 1
                    last_peak = i
    
    return round((peaks / duration_sec) * 60)

# --- בייסליין ---
print("שים אצבע - מודד בייסליין 10 שניות...")
time.sleep(2)
baseline = measure_bpm(30)
print(f"דופק בייסליין: {baseline} BPM")

# --- עם לחץ ---
input("\nלחץ Enter כשמוכן להפעיל את האזעקה...")
print("מודד עם לחץ 10 שניות...")
stress = measure_bpm(30)
print(f"דופק תחת לחץ: {stress} BPM")

# --- תוצאה ---
diff = stress - baseline
print(f"\n תוצאות:")
print(f"בייסליין:  {baseline} BPM")
print(f"תחת לחץ:  {stress} BPM")
print(f"הפרש:      {diff:+d} BPM")

if diff > 10:
    print("זוהתה עלייה משמעותית בדופק!")
elif diff > 0:
    print("זוהתה עלייה קלה בדופק")
else:
    print("לא זוהתה עלייה בדופק")
