# ZundaTalk

VOICEVOXを使用したブラウザアバターとOBS用字幕オーバーレイ。

## 機能
- VOICEVOXで音声を生成
- WebSocket経由でアバターと字幕ウィンドウを操作
- `config.json`で駆動する入力モード選択（手動またはChrome音声認識）
- シンプルな感情切り替えでアバター表情を変更

## セットアップ
1. `setup.bat`を実行
2. VOICEVOXを開始
3. 必要に応じて`ZundaTalk/config.json`を編集
4. `run.bat`を実行
5. ブラウザで以下のページを開く：
   - `http://localhost:8000/avatar.html`
   - `http://localhost:8000/subtitle.html`
   - `http://localhost:8000/recognizer.html`（`input.mode`が`chrome`の場合）

## 注記
- `input.mode`を`manual`または`chrome`に設定
- `manual`モードでは`input.manual_ws_port`を使用して、入力WebSocketポートを選択可能
- `chrome`モードは常にWebSocketポート`8080`を使用
- Chrome音声認識はブラウザのWeb Speech API（`webkitSpeechRecognition`）を使用
- `chrome`モードでは、`run.bat`がChromeを自動的に起動し、`recognizer.html?autostart=1`を開く

## ライセンス
MIT License
