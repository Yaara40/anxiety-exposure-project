import time
import subprocess
import threading
import requests
import os
import argparse
from sensor.bpm_graph import measure_baseline, run_graph, freeze_graph

VIDEOS_DIR = "/home/pi/anxiety_project/videos/"
VLC_PASSWORD = "1234"
EXPOSURE_PORT = 9000
CALMING_PORT = 9001
CALMING_DURATION = 10
SWITCH_DELAY = 7

VLC_X = 0
VLC_Y = 62
VLC_W = 640
VLC_H = 1040

VLC_ENV = {**os.environ, 'DISPLAY': ':0', 'QT_QPA_PLATFORM': 'xcb', 'WAYLAND_DISPLAY': ''}

def vlc_command(port, command):
    try:
        requests.get(
            f"http://localhost:{port}/requests/status.json?command={command}",
            auth=("", VLC_PASSWORD),
            timeout=2
        )
    except Exception as e:
        print(f"VLC command error (port {port}): {e}")

def position_vlc():
    def _move():
        time.sleep(5)
        result = subprocess.run(
            ['bash', '-c', f'DISPLAY=:0 xdotool search --name "VLC media player" windowmove {VLC_X} {VLC_Y} windowsize {VLC_W} {VLC_H}'],
            capture_output=True, text=True
        )
        print(f"xdotool result: {result.returncode} {result.stderr.strip()}")
    threading.Thread(target=_move, daemon=True).start()

def vlc_base_args(port):
    return [
        'vlc',
        '--intf', 'http',
        '--http-host', 'localhost',
        '--http-port', str(port),
        '--http-password', VLC_PASSWORD,
        '--no-osd',
        '--no-video-title-show',
        '--no-qt-fs-controller',
        '--no-fullscreen',
        '--qt-minimal-view',
        '--no-qt-system-tray',
    ]

def launch_exposure(video_file):
    subprocess.Popen(
        vlc_base_args(EXPOSURE_PORT) + ['--start-paused', VIDEOS_DIR + video_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=VLC_ENV
    )
    position_vlc()

def launch_calming_hidden():
    subprocess.Popen(
        vlc_base_args(CALMING_PORT) + ['--start-paused', '--no-video', VIDEOS_DIR + "calming.mp4"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=VLC_ENV
    )

def launch_calming_visible():
    subprocess.Popen(
        vlc_base_args(CALMING_PORT) + ['--start-paused', '--no-embedded-video', VIDEOS_DIR + "calming.mp4"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=VLC_ENV
    )
    position_vlc()

def kill_vlc(port):
    subprocess.run(
        ['pkill', '-f', f'http-port {port}'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)

def choose_session():
    minutes = input("Session duration (minutes): ").strip()
    try:
        minutes = int(minutes)
    except:
        minutes = 5
    return minutes

def main():
    # Parse command line arguments from api.py
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', type=str, default=None)
    parser.add_argument('--duration', type=int, default=None)
    parser.add_argument('--baseline', type=int, default=None)
    args = parser.parse_args()

    print("=== Anxiety Exposure Therapy System ===\n")

    # If called from API, skip interactive input
    if args.baseline is not None:
        baseline = args.baseline
        print(f"Baseline (from API): {baseline} BPM")
    else:
        baseline = measure_baseline()

    if args.duration is not None:
        duration_minutes = args.duration
        print(f"Duration (from API): {duration_minutes} minutes")
    else:
        duration_minutes = choose_session()

    video_file = args.video if args.video else "exposure.mp4"

    print(f"\nLoading videos, please wait...")
    launch_exposure(video_file)
    time.sleep(5)
    launch_calming_hidden()
    time.sleep(3)

    print("Starting session...")

    in_anxiety = [False]

    def on_anxiety_detected():
        if in_anxiety[0]:
            return
        in_anxiety[0] = True
        print("Anxiety detected - switching to calming video")

        freeze_graph(SWITCH_DELAY)
        vlc_command(EXPOSURE_PORT, "pl_pause")

        kill_vlc(CALMING_PORT)
        launch_calming_visible()
        time.sleep(3)
        vlc_command(CALMING_PORT, "fullscreen&val=0")
        vlc_command(CALMING_PORT, "pl_play")

        time.sleep(CALMING_DURATION)

        freeze_graph(SWITCH_DELAY)
        kill_vlc(CALMING_PORT)
        launch_calming_hidden()
        time.sleep(3)
        vlc_command(EXPOSURE_PORT, "pl_play")

        in_anxiety[0] = False
        print("Resumed exposure video")

    def delayed_start():
        time.sleep(3)
        vlc_command(EXPOSURE_PORT, "pl_play")
        print("Exposure video started")

    threading.Thread(target=delayed_start, daemon=True).start()

    run_graph(baseline, duration_minutes, on_anxiety_detected)

    print("Killing VLC instances...")
    kill_vlc(CALMING_PORT)
    kill_vlc(EXPOSURE_PORT)
    print("\nSession complete!")

if __name__ == "__main__":
    main()
