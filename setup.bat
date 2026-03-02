@echo off
REM Python仮想環境の作成と依存パッケージのインストール
cd /d %~dp0
python -m venv env
call env\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
pause
