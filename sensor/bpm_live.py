# sensor/bpm_live_fake.py

import time

WINDOW_SIZE = 500

_fake_start_time = None

_fake_bpm_sequence = [
    # Baseline measurement (0-5 sec)
    (0,  62),
    (3,  63),

    # Graph opens, video starts at ~10 sec
    # 18 sec normal after video starts = around sec 28 total
    (10, 62),
    (13, 63),
    (16, 61),
    (19, 62),
    (22, 63),
    (25, 62),

    # Rising BPM (sec 28-35)
    (28, 68),
    (29, 72),
    (30, 76),
    (31, 80),
    (32, 85),
    (33, 90),

    # Calming video plays (10 sec) - BPM goes down (sec 35-45)
    (35, 80),
    (37, 72),
    (39, 68),
    (41, 64),
    (43, 62),

    # Resume exposure - normal (sec 45-70)
    (45, 62),
    (50, 63),
    (55, 62),
    (60, 61),
    (65, 63),

    # Rising again (sec 70-77)
    (70, 68),
    (71, 72),
    (72, 76),
    (73, 80),
    (74, 85),
    (75, 90),

    # Calming (sec 77-87)
    (77, 80),
    (79, 72),
    (81, 68),
    (83, 64),
    (85, 62),

    # Normal until end (sec 87-120)
    (87, 62),
    (95, 63),
    (100, 62),
    (110, 63),
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
