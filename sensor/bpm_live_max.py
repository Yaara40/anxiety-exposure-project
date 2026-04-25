import time
import smbus2
import numpy as np
import threading
from collections import deque

MAX30100_ADDRESS = 0x57
WINDOW_SIZE = 500

bus = smbus2.SMBus(1)
_lock = threading.Lock()
_sample_buffer = deque(maxlen=WINDOW_SIZE)
_running = False
_last_init = [0]

def write_register(reg, value):
    bus.write_byte_data(MAX30100_ADDRESS, reg, value)

def read_register(reg):
    return bus.read_byte_data(MAX30100_ADDRESS, reg)

def initialize():
    try:
        write_register(0x06, 0x40)
        time.sleep(0.2)
        write_register(0x02, 0x00)
        write_register(0x03, 0x00)
        write_register(0x04, 0x00)
        write_register(0x06, 0x03)
        write_register(0x07, 0x47)
        write_register(0x09, 0xFF)
        write_register(0x01, 0xF0)
        time.sleep(0.1)
        return True
    except Exception as e:
        print(f"Init error: {e}")
        return False

def _reader_thread():
    global _running
    while _running:
        try:
            read_register(0x00)
            wr = read_register(0x02)
            rd = read_register(0x04)
            num = (wr - rd) & 0x0F
            for _ in range(num):
                data = bus.read_i2c_block_data(MAX30100_ADDRESS, 0x05, 4)
                ir = (data[0] << 8) | data[1]
                if 1000 < ir < 65000:
                    with _lock:
                        _sample_buffer.append(ir)
        except Exception:
            if time.time() - _last_init[0] > 2.0:
                try:
                    initialize()
                    _last_init[0] = time.time()
                except:
                    pass
        time.sleep(0.005)

def start_reader():
    global _running
    _running = True
    t = threading.Thread(target=_reader_thread, daemon=True)
    t.start()
    print("Sensor reader thread started")

def read_adc(channel=0):
    with _lock:
        if _sample_buffer:
            return _sample_buffer[-1]
    return None

def calculate_bpm(values):
    values = [v for v in values if v is not None]
    if len(values) < 100:
        return None
    try:
        signal = np.array(values, dtype=float)
        sample_rate = 60.0
        signal = signal - np.mean(signal)

        from scipy.signal import butter, filtfilt
        nyq = sample_rate / 2.0
        low = 0.5 / nyq
        high = min(3.0 / nyq, 0.99)
        b, a = butter(2, [low, high], btype='band')
        filtered = filtfilt(b, a, signal)

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
_last_init[0] = time.time()
start_reader()