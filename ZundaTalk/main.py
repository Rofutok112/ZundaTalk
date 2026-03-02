import asyncio
import json
import os
import socket
import threading
import websockets

import server

# 設定ファイルの読み込み
_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(_config_path, encoding="utf-8") as _f:
    _config = json.load(_f)

VV_HOST = _config["voicevox"]["host"]
VV_PORT = _config["voicevox"]["port"]
SPEAKER_ID = _config["voicevox"]["speaker_id"]
WS_PORT = _config["server"]["ws_port"]
HTTP_PORT = _config["server"]["http_port"]


def is_vv_running(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


async def main():
    handler = server.make_handler(VV_HOST, VV_PORT, SPEAKER_ID)
    async with websockets.serve(handler, "0.0.0.0", WS_PORT):
        print(f"WebSocketサーバーがポート{WS_PORT}で起動しました...")
        print("接続を待機中...")
        await asyncio.Future()


if __name__ == "__main__":
    if not is_vv_running(VV_HOST, VV_PORT):
        print("[ERROR] VOICEVOXエンジンを起動してから、もう一度実行してください")
        exit()

    http_thread = threading.Thread(target=lambda: server.start_http_server(HTTP_PORT), daemon=True)
    http_thread.start()

    asyncio.run(main())