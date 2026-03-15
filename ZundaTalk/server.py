import base64
import http.server
import json
import os
import socketserver
import threading

import requests
import websockets

CHROME_WS_PORT = 8080


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def handle(self):
        try:
            super().handle()
        except ConnectionAbortedError:
            pass
        except Exception:
            pass


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def create_http_server(http_port):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    return ReusableTCPServer(("", http_port), QuietHandler)


def start_http_server(httpd, input_mode, ws_port):
    print(f"   Avatar:     http://localhost:{httpd.server_address[1]}/avatar.html")
    print(f"   Subtitle:   http://localhost:{httpd.server_address[1]}/subtitle.html")
    if input_mode == "chrome":
        print(f"   Recognizer: http://localhost:{httpd.server_address[1]}/recognizer.html")
        print(f"   Input WS:   {ws_port} (fixed for chrome mode)")
    else:
        print(f"   Input WS:   {ws_port} (configurable manual mode)")
    try:
        httpd.serve_forever()
    except Exception:
        pass


def shutdown_http_server(httpd, thread):
    if httpd is None:
        return

    httpd.shutdown()
    httpd.server_close()

    if thread is not None and thread.is_alive():
        thread.join(timeout=2.0)


def generate_voice(text, vv_host, vv_port, speaker_id):
    query_res = requests.post(
        f"http://{vv_host}:{vv_port}/audio_query",
        params={"text": text, "speaker": speaker_id}
    )
    query_data = query_res.json()

    synth_res = requests.post(
        f"http://{vv_host}:{vv_port}/synthesis",
        params={"speaker": speaker_id},
        json=query_data
    )
    audio_bytes = synth_res.content

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return audio_b64, query_data


def make_handler(vv_host, vv_port, speaker_id, emotion_analyzer=None):
    connected_clients = set()

    async def handler(websocket):
        connected_clients.add(websocket)
        print(f"[ws] client connected (clients={len(connected_clients)})")

        try:
            async for message in websocket:
                audio_b64, query_data = generate_voice(message, vv_host, vv_port, speaker_id)

                if emotion_analyzer is not None:
                    emotion = emotion_analyzer.analyze(message)
                else:
                    emotion = "normal"

                reply_data = {
                    "type": "play_voice",
                    "text": message,
                    "audio_b64": audio_b64,
                    "query": query_data,
                    "emotion": emotion,
                }

                for client in connected_clients:
                    await client.send(json.dumps(reply_data))

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            connected_clients.remove(websocket)

    return handler
