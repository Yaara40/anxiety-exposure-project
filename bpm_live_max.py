# sensor/bpm_live_max.py
import time
import smbus2
import numpy as np
from collections import deque

MAX30100_ADDRESS = 0x57
WINDOW_SIZE = 500

bus = smbus2.SMBus(1)

def write_register(reg, value):
    bus.write_byte_data(MAX30100_ADDRESS, reg, value)

def read_register(reg):
    return bus.read_byte_data(MAX30100_ADDRESS, reg)

def initialize():
    try:
        write_register(0x06, 0x40)  # Reset
        time.sleep(0.1)
        write_register(0x02, 0x00)  # Clear FIFO
        write_register(0x03, 0x00)
        write_register(0x04, 0x00)
        write_register(0x06, 0x03)  # SPO2 mode
        write_register(0x07, 0x47)  # 100Hz, 1600us pulse width
        write_register(0x09, 0xFF)  # Max LED current
        write_register(0x01, 0xF0)  # Enable interrupts
        print("MAX30100 initialized")
        return True
    except Exception as e:
        print(f"Init error: {e}")
        return False

def read_adc(channel=0):
    try:
        wr = read_register(0x02)
        rd = read_register(0x04)
        num = (wr - rd) & 0x0F
        if num == 0:
            return None
        # Drain all available samples, return the last one
        val = None
        for _ in range(num):
            data = bus.read_i2c_block_data(MAX30100_ADDRESS, 0x05, 4)
            ir = (data[0] << 8) | data[1]
            if ir < 65535:  # ignore saturated values
                val = ir
        return val
    except Exception as e:
        return None

def calculate_bpm(values):
    values = [v for v in values if v is not None and v < 65535]
    if len(values) < 100:
        return None
    try:
        signal = np.array(values, dtype=float)
        sample_rate = 60.0  # approximate Hz

        # Remove DC offset
        signal = signal - np.mean(signal)

        # Bandpass filter: keep 0.5-3.0 Hz (30-180 BPM)
        from scipy.signal import butter, filtfilt
        nyq = sample_rate / 2.0
        low = 0.5 / nyq
        high = 3.0 / nyq
        high = min(high, 0.99)
        b, a = butter(2, [low, high], btype='band')
        filtered = filtfilt(b, a, signal)

        # Find peaks
        threshold = np.std(filtered) * 0.3
        peaks = []
        min_distance = int(sample_rate * 0.4)
        i = 1
        while i < len(filtered) - 1:
            if (filtered[i] > threshold and
                filtered[i] > filtered[i-1] and
                filtered[i] > filtered[i+1]):
                if not peaks or (i - peaks[-1]) > min_distance:
                    peaks.append(i)
            i += 1

        if len(peaks) < 2:
            return None

        intervals = np.diff(peaks)
        avg_interval = np.mean(intervals)
        bpm = (sample_rate / avg_interval) * 60

        if 40 <= bpm <= 180:
            return int(bpm)
        return None

    except Exception as e:
        print(f"calculate_bpm error: {e}")
        return None

initialize()