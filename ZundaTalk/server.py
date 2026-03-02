import websockets
import json
import requests
import base64
import http.server
import socketserver
import os


def start_http_server(http_port):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

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

    with ReusableTCPServer(("", http_port), QuietHandler) as httpd:
        print(f"   ▶ 立ち絵: http://localhost:{http_port}/avatar.html")
        print(f"   ▶ 字幕:   http://localhost:{http_port}/subtitle.html")
        httpd.serve_forever()


def generate_voice(text, vv_host, vv_port, speaker_id):
    # クエリ作成
    query_res = requests.post(f"http://{vv_host}:{vv_port}/audio_query", params={"text": text, "speaker": speaker_id})
    query_data = query_res.json()

    # 音声データ合成
    synth_res = requests.post(f"http://{vv_host}:{vv_port}/synthesis", params={"speaker": speaker_id}, json=query_data)
    audio_bytes = synth_res.content

    # wav -> Base64変換
    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

    return audio_b64, query_data


def make_handler(vv_host, vv_port, speaker_id):
    connected_clients = set()

    async def handler(websocket):
        connected_clients.add(websocket)
        print(f"[接続] 新しいクライアントにつながりました。（現在: {len(connected_clients)}台）")

        try:
            async for message in websocket:
                audio_b64, query_data = generate_voice(message, vv_host, vv_port, speaker_id)

                reply_data = {
                    "type": "play_voice",
                    "text": message,
                    "audio_b64": audio_b64,
                    "query": query_data
                }

                for client in connected_clients:
                    await client.send(json.dumps(reply_data))

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            # 接続が切れたらリストから削除
            connected_clients.remove(websocket)

    return handler