import threading
import time
import subprocess
import requests as http_requests
import os
from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from flask_cors import CORS

from sensor.bpm_live_max import _sample_buffer, _lock, calculate_bpm

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

session_state = {
    "running": False,
    "scenario_id": None,
    "duration_minutes": 0,
    "current_bpm": None,
    "status": "idle",
    "time_remaining": 0,
    "baseline": 70,
}

SCENARIO_VIDEOS = {
    "heights": "exposure.mp4",
    "underwater": "exposure.mp4",
    "extreme-weather": "exposure.mp4",
    "fire": "exposure.mp4",
    "roller-coaster": "exposure.mp4",
    "squid-game": "exposure.mp4",
}

_session_process = [None]

def bpm_broadcaster():
    while True:
        with _lock:
            samples = list(_sample_buffer)
        bpm = calculate_bpm(samples)
        session_state["current_bpm"] = bpm

        # Infer status from BPM vs baseline
        if session_state["running"] and bpm:
            baseline = session_state.get("baseline", 70)
            threshold = baseline * 1.08
            if bpm >= threshold:
                session_state["status"] = "calming"
            else:
                if session_state["status"] == "calming":
                    session_state["status"] = "running"

        socketio.emit('bpm_update', {
            'bpm': bpm,
            'status': session_state['status'],
            'time_remaining': session_state['time_remaining']
        })
        time.sleep(1)

def run_session(video_file, duration_minutes, baseline):
    session_state["running"] = True
    session_state["status"] = "running"

    env = {**os.environ, 'DISPLAY': ':0', 'QT_QPA_PLATFORM': 'xcb', 'WAYLAND_DISPLAY': ''}

    process = subprocess.Popen(
        ['python3', '/home/pi/anxiety_project/main.py',
         '--video', video_file,
         '--duration', str(duration_minutes),
         '--baseline', str(baseline)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    _session_process[0] = process

    # Wait for session to actually start before counting down
    time.sleep(10)

    duration_seconds = duration_minutes * 60
    start_time = time.time()

    while session_state["running"]:
        elapsed = time.time() - start_time
        remaining = max(0, int(duration_seconds - elapsed))
        session_state["time_remaining"] = remaining
        if remaining <= 0:
            break
        time.sleep(1)

    _session_process[0] = None
    session_state["running"] = False
    session_state["status"] = "complete"
    session_state["time_remaining"] = 0
    socketio.emit('session_complete', {'message': 'Session complete!'})

@app.route('/session/start', methods=['POST'])
def start_session():
    if session_state["running"]:
        return jsonify({"error": "Session already running"}), 400

    data = request.json
    scenario_id = data.get("scenario_id")
    duration = data.get("duration_minutes", 1)
    baseline = data.get("baseline", 70)

    video_file = SCENARIO_VIDEOS.get(scenario_id, "exposure.mp4")

    session_state["scenario_id"] = scenario_id
    session_state["duration_minutes"] = duration
    session_state["baseline"] = baseline
    session_state["status"] = "starting"
    session_state["time_remaining"] = duration * 60

    threading.Thread(
        target=run_session,
        args=(video_file, duration, baseline),
        daemon=True
    ).start()

    return jsonify({"message": "Session started", "scenario_id": scenario_id, "duration": duration})

@app.route('/session/stop', methods=['POST'])
def stop_session():
    session_state["running"] = False
    if _session_process[0]:
        _session_process[0].terminate()
    subprocess.run(['pkill', '-f', 'http-port 9000'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-f', 'http-port 9001'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    session_state["status"] = "idle"
    return jsonify({"message": "Session stopped"})

@app.route('/session/status', methods=['GET'])
def get_status():
    with _lock:
        samples = list(_sample_buffer)
    bpm = calculate_bpm(samples)
    return jsonify({
        "running": session_state["running"],
        "status": session_state["status"],
        "bpm": bpm,
        "time_remaining": session_state["time_remaining"],
        "scenario_id": session_state["scenario_id"],
    })

@app.route('/baseline/start', methods=['POST'])
def start_baseline():
    def measure():
        session_state["status"] = "measuring_baseline"
        time.sleep(15)
        with _lock:
            samples = list(_sample_buffer)
        bpm = calculate_bpm(samples)
        session_state["baseline"] = bpm or 70
        session_state["status"] = "idle"
        socketio.emit('baseline_ready', {'baseline': session_state["baseline"]})
    threading.Thread(target=measure, daemon=True).start()
    return jsonify({"message": "Baseline measurement started"})

@app.route('/baseline/value', methods=['GET'])
def get_baseline_value():
    return jsonify({"baseline": session_state.get("baseline", 70)})

if __name__ == '__main__':
    threading.Thread(target=bpm_broadcaster, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
