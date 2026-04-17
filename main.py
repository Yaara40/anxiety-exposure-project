import time
import subprocess
import threading
import requests
from sensor.bpm_graph import measure_baseline, run_graph, freeze_graph

VIDEOS_DIR = "/home/pi/anxiety_project/videos/"
VLC_PASSWORD = "1234"
EXPOSURE_PORT = 9000
CALMING_PORT = 9001
CALMING_DURATION = 10      # adjust to your calming video length in seconds
SWITCH_DELAY = 7           # seconds it takes to kill/launch VLC - freeze graph for this long

def vlc_command(port, command):
    try:
        requests.get(
            f"http://localhost:{port}/requests/status.json?command={command}",
            auth=("", VLC_PASSWORD),
            timeout=2
        )
    except Exception as e:
        print(f"VLC command error (port {port}): {e}")

def launch_exposure():
    subprocess.Popen(
        ['vlc',
         '--start-paused',
         '--intf', 'http',
         '--http-host', 'localhost',
         '--http-port', str(EXPOSURE_PORT),
         '--http-password', VLC_PASSWORD,
         VIDEOS_DIR + "exposure.mp4"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def launch_calming_hidden():
    subprocess.Popen(
        ['vlc',
         '--start-paused',
         '--no-video',
         '--intf', 'http',
         '--http-host', 'localhost',
         '--http-port', str(CALMING_PORT),
         '--http-password', VLC_PASSWORD,
         VIDEOS_DIR + "calming.mp4"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def launch_calming_visible():
    subprocess.Popen(
        ['vlc',
         '--intf', 'http',
         '--http-host', 'localhost',
         '--http-port', str(CALMING_PORT),
         '--http-password', VLC_PASSWORD,
         VIDEOS_DIR + "calming.mp4"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

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
    print("=== Anxiety Exposure Therapy System ===\n")
    baseline = measure_baseline()
    duration_minutes = choose_session()

    print(f"\nLoading videos, please wait...")
    launch_exposure()
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

        # Freeze graph to match video switching delay
        freeze_graph(SWITCH_DELAY)

        # Pause exposure
        vlc_command(EXPOSURE_PORT, "pl_pause")

        # Kill hidden calming, reopen with video
        kill_vlc(CALMING_PORT)
        launch_calming_visible()
        time.sleep(5)
        vlc_command(CALMING_PORT, "pl_play")

        # Wait for calming video to finish
        time.sleep(CALMING_DURATION)

        # Freeze graph again for switch back delay
        freeze_graph(SWITCH_DELAY)

        # Kill visible calming, reopen hidden, resume exposure
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

    # This blocks until session ends
    run_graph(baseline, duration_minutes, on_anxiety_detected)

    # Session complete - kill both VLC instances
    kill_vlc(CALMING_PORT)
    kill_vlc(EXPOSURE_PORT)
    print("\nSession complete!")

if __name__ == "__main__":
    main()
