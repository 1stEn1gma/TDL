@echo off
set /p param1="Введите значение параметра param1: "

start cmd.exe /k "venv\Scripts\activate && uvicorn src.main:app --reload --host %param1%"