# main.py
import time
import subprocess
import threading
from sensor.bpm_graph import measure_baseline, run_graph

VIDEOS_DIR = "/home/pi/anxiety_project/videos/"

def choose_session():
    minutes = input("Session duration (minutes): ").strip()
    try:
        minutes = int(minutes)
    except:
        minutes = 5
    return "exposure.mp4", minutes

def play_video(filename):
    process = subprocess.Popen(
        ['vlc',
         '--no-osd',
         '--no-video-title-show',
         '--avcodec-threads', '1',
         '--width', '640',
         '--height', '1024',
         '--no-qt-fs-controller',
         '--qt-minimal-view',
         '--no-qt-system-tray',
         VIDEOS_DIR + filename],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    def move_window():
        time.sleep(2)
        subprocess.Popen(['wmctrl', '-r', 'VLC', '-e', '0,0,0,640,1024'])
    threading.Thread(target=move_window, daemon=True).start()
    return process

def stop_video(process):
    if process:
        process.terminate()
        process.wait()

def main():
    print("=== Anxiety Exposure Therapy System ===\n")
    baseline = measure_baseline()
    video_file, duration_minutes = choose_session()
    print(f"\nStarting session: {video_file} | {duration_minutes} minutes")
    input("Press Enter to begin...")

    video_process = [None]
    calming_process = [None]

    # Track exposure position
    exposure_start_time = [None]
    exposure_elapsed = [0]

    def on_anxiety_detected():
        print("Anxiety detected - switching to calming video")
        if exposure_start_time[0]:
            exposure_elapsed[0] += time.time() - exposure_start_time[0]
            exposure_start_time[0] = None
        print(f"Saved position: {exposure_elapsed[0]:.1f} seconds")
        stop_video(video_process[0])
        calming_process[0] = play_video("calming.mp4")
        time.sleep(10)
        stop_video(calming_process[0])
        print(f"Resuming from: {exposure_elapsed[0]:.1f} seconds")
        video_process[0] = play_video(video_file)
        exposure_start_time[0] = time.time()

    def delayed_video():
        time.sleep(10)
        exposure_start_time[0] = time.time()
        video_process[0] = play_video(video_file)

    threading.Thread(target=delayed_video, daemon=True).start()

    run_graph(baseline, duration_minutes, on_anxiety_detected)

    stop_video(video_process[0])
    stop_video(calming_process[0])
    print("\nSession complete!")

if __name__ == "__main__":
    main()
