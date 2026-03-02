import asyncio
import websockets
import json
import requests
import base64
import threading
import http.server
import socketserver
import os

connected_clients = set()

# VOICEVOXの設定
VV_HOST = "127.0.0.1"
VV_PORT = 50021
SPEAKER_ID = 3  # ずんだもん

def start_http_server():
    PORT = 8000
    
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
    
    with ReusableTCPServer(("", PORT), QuietHandler) as httpd:
        print(f"   ▶ 立ち絵: http://localhost:{PORT}/avatar.html")
        print(f"   ▶ 字幕:   http://localhost:{PORT}/subtitle.html")
        httpd.serve_forever()

def generate_voice(text):
    # クエリ作成
    query_res = requests.post(f"http://{VV_HOST}:{VV_PORT}/audio_query", params={"text": text, "speaker": SPEAKER_ID})
    query_data = query_res.json()
    
    # 音声データ合成
    synth_res = requests.post(f"http://{VV_HOST}:{VV_PORT}/synthesis", params={"speaker": SPEAKER_ID}, json=query_data)
    audio_bytes = synth_res.content

    # wav -> Base64変換
    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    return audio_b64, query_data


async def handler(websocket):
    connected_clients.add(websocket)
    print(f"[接続] 新しいクライアントにつながりました。（現在: {len(connected_clients)}台）")

    try:
        async for message in websocket:
            audio_b64, query_data = generate_voice(message)

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

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8080):
        print("WebSocketサーバーがポート8080で起動しました...")
        print("接続を待機中...")
        await asyncio.Future()  # サーバーを永遠に動かし続ける

if __name__ == "__main__":
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()

    asyncio.run(main())