@echo off
REM Python仮想環境の作成と依存パッケージのインストール
cd /d %~dp0

python -m venv env

call env\Scripts\activate.bat

python -m pip install --upgrade pip
python -m pip install -r ZundaTalk/requirements.txt

pause