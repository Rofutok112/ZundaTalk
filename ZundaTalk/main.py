import asyncio
import json
import os
import shutil
import socket
import signal
import subprocess
import tempfile
import threading
import time

import websockets

import server

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_PATH, encoding="utf-8") as config_file:
    CONFIG = json.load(config_file)

CHROME_PROFILE_PREFIX = "zundatalk-chrome-"
CHROME_PROFILE_ROOT = os.path.join(tempfile.gettempdir(), "zundatalk-chrome-profiles")
VV_HOST = CONFIG["voicevox"]["host"]
VV_PORT = CONFIG["voicevox"]["port"]
SPEAKER_ID = CONFIG["voicevox"]["speaker_id"]
HTTP_PORT = CONFIG["server"]["http_port"]
EMOTION_ENABLED = CONFIG.get("emotion", {}).get("enabled", False)
INPUT_MODE = CONFIG.get("input", {}).get("mode", "manual")
MANUAL_WS_PORT = CONFIG.get("input", {}).get(
    "manual_ws_port",
    CONFIG.get("server", {}).get("ws_port", 8080)
)
WS_PORT = server.CHROME_WS_PORT if INPUT_MODE == "chrome" else MANUAL_WS_PORT


def is_vv_running(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((host, port)) == 0


def find_chrome_executable():
    for command_name in (
        "chrome",
        "chrome.exe",
        "google-chrome",
        "Google Chrome",
        "chromium",
        "chromium-browser",
    ):
        chrome_path = shutil.which(command_name)
        if chrome_path:
            return chrome_path

    local_app_data = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("PROGRAMFILES", "")
    program_files_x86 = os.environ.get("PROGRAMFILES(X86)", "")

    candidates = [
        os.path.join(local_app_data, "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(program_files_x86, "Google", "Chrome", "Application", "chrome.exe"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate

    return None


def cleanup_stale_chrome_profiles():
    if not os.path.isdir(CHROME_PROFILE_ROOT):
        return

    for entry in os.scandir(CHROME_PROFILE_ROOT):
        if not entry.is_dir():
            continue
        if not entry.name.startswith(CHROME_PROFILE_PREFIX):
            continue
        shutil.rmtree(entry.path, ignore_errors=True)


def launch_chrome_recognizer(http_port):
    chrome_executable = find_chrome_executable()
    if not chrome_executable:
        print("[chrome] Chrome executable was not found. Open recognizer.html manually.")
        return None, None

    recognizer_url = f"http://localhost:{http_port}/recognizer.html?autostart=1"
    os.makedirs(CHROME_PROFILE_ROOT, exist_ok=True)
    profile_dir = tempfile.mkdtemp(prefix=CHROME_PROFILE_PREFIX, dir=CHROME_PROFILE_ROOT)
    time.sleep(1.0)
    process = subprocess.Popen([
        chrome_executable,
        f"--app={recognizer_url}",
        "--new-window",
        "--window-size=360,220",
        "--window-position=20,20",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
    ])
    print(f"[chrome] launched recognizer: {recognizer_url}")
    return process, profile_dir


def shutdown_chrome_recognizer(process, profile_dir):
    if process is not None and process.poll() is None:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    if profile_dir and os.path.isdir(profile_dir):
        shutil.rmtree(profile_dir, ignore_errors=True)


def shutdown_services(httpd, http_thread, chrome_process, chrome_profile_dir):
    server.shutdown_http_server(httpd, http_thread)
    shutdown_chrome_recognizer(chrome_process, chrome_profile_dir)


def install_shutdown_handlers(stop_event):
    def handle_shutdown_signal(signum, frame):
        del frame
        print(f"\n[shutdown] received signal {signum}, stopping...")
        stop_event.set()

    signal.signal(signal.SIGINT, handle_shutdown_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_shutdown_signal)


async def main(stop_event):
    emotion_analyzer = None
    if EMOTION_ENABLED:
        from emotion_analyzer import EmotionAnalyzer
        emotion_analyzer = EmotionAnalyzer()
    else:
        print("[emotion] disabled")

    handler = server.make_handler(VV_HOST, VV_PORT, SPEAKER_ID, emotion_analyzer)
    async with websockets.serve(handler, "0.0.0.0", WS_PORT):
        print(f"WebSocket server listening on port {WS_PORT} (mode={INPUT_MODE})")
        print("Waiting for input...")
        while not stop_event.is_set():
            await asyncio.sleep(0.2)


if __name__ == "__main__":
    if not is_vv_running(VV_HOST, VV_PORT):
        print("[ERROR] Start the VOICEVOX engine first.")
        raise SystemExit(1)

    cleanup_stale_chrome_profiles()

    httpd = server.create_http_server(HTTP_PORT)
    http_thread = threading.Thread(
        target=server.start_http_server,
        args=(httpd, INPUT_MODE, WS_PORT),
        daemon=True
    )
    http_thread.start()

    chrome_process = None
    chrome_profile_dir = None
    if INPUT_MODE == "chrome":
        chrome_process, chrome_profile_dir = launch_chrome_recognizer(HTTP_PORT)

    stop_event = threading.Event()
    install_shutdown_handlers(stop_event)

    try:
        asyncio.run(main(stop_event))
    except KeyboardInterrupt:
        print("\n[shutdown] keyboard interrupt received, stopping...")
        stop_event.set()
    finally:
        shutdown_services(httpd, http_thread, chrome_process, chrome_profile_dir)
