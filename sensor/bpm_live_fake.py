# sensor/bpm_live_fake.py

import time

WINDOW_SIZE = 500

_fake_start_time = None

_fake_bpm_sequence = [
    # 0-20 sec: baseline measurement - normal (60-64)
    (0,  62),
    (5,  60),
    (10, 63),
    (15, 61),

    # 20-40 sec: session starts - normal
    (20, 62),
    (25, 63),
    (30, 64),
    (35, 62),

    # 40-55 sec: anxiety event 1 (75-90)
    (40, 75),
    (43, 82),
    (46, 88),
    (49, 90),
    (52, 87),

    # 55-75 sec: calming (66-62)
    (55, 66),
    (58, 64),
    (61, 63),
    (64, 62),
    (70, 62),

    # 75-95 sec: anxiety event 2 (75-95)
    (75, 75),
    (78, 85),
    (81, 90),
    (84, 95),
    (87, 88),

    # 95-120 sec: calming back to normal
    (95,  66),
    (98,  64),
    (101, 63),
    (104, 62),
    (120, 62),
]

def read_adc(channel):
    """Fake read - not used but kept for API compatibility"""
    return 213

def calculate_bpm(values):
    """Return fake BPM based on scenario timeline"""
    global _fake_start_time

    if _fake_start_time is None:
        _fake_start_time = time.time()

    elapsed = time.time() - _fake_start_time
    current_bpm = _fake_bpm_sequence[0][1]
    for t, bpm in _fake_bpm_sequence:
        if elapsed >= t:
            current_bpm = bpm
        else:
            break

    return current_bpm
