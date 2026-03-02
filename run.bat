@echo off
REM 仮想環境を有効化し、サーバーを起動
cd /d %~dp0
call env\Scripts\activate.bat
python ZundaTalk\server.py
pause
