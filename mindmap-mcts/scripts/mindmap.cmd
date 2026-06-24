@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%"
set "PYTHONIOENCODING=utf-8"
python -m mindmap_mcts.cli %*
if errorlevel 1 exit /b %errorlevel%
