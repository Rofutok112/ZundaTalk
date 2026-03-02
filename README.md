# ZundaTalk

ずんだもんの音声合成・アバター・字幕をWebで連携する簡易システムです。
OBSのブラウザソースで使用することを想定しています。

## 機能
- VOICEVOXによる音声合成
- WebSocketで音声・字幕・アバターを同期
- 口パク・まばたきアニメーション
- サーバー・クライアント一式同梱

## 必要環境
- Python 3.8以降
- VOICEVOXエンジン（ローカルで起動しておく）
- Windows（推奨）
- OBS

## セットアップ
1. 仮想環境の作成（初回のみ）
   ```
   python -m venv env
   env\Scripts\activate
   pip install -r requirements.txt
   ```
2. VOICEVOXエンジンを起動
3. `start_server.bat` をダブルクリック
4. `avatar.html` と `subtitle.html` をブラウザで開く

## ファイル構成
- Scripts/
  - server.py ... WebSocketサーバー
  - avatar.js, avatar.html ... アバター表示, 音声再生
  - subtitle.js, subtitle.html ... 字幕表示
- Images/ ... 口・目画像
- env/ ... Python仮想環境

## ライセンス
MIT License

---

ご自由に改造・利用してください。
