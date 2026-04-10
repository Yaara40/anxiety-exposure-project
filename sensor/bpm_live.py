# sensor/bpm_live.py
import spidev

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
