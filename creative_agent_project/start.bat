@echo off
REM 智能资料整理助手 — 启动脚本
REM 对应第10章：轻量级交付

set COURSE_API_TOKEN=dev-local-token
set OPENAI_API_KEY=sk-your-key-here
set OPENAI_BASE_URL=https://api.openai.com/v1
set MODEL_NAME=gpt-4o-mini
set PORT=8000

echo ========================================
echo   智能资料整理助手 (Smart Doc Organizer)
echo ========================================
echo.
echo   API 文档: http://127.0.0.1:%PORT%/docs
echo   前端页面: 双击 index.html
echo   烟测命令: python smoke_api.py http://127.0.0.1:%PORT% dev-local-token
echo.

uvicorn src.app:app --host 0.0.0.0 --port %PORT% --reload
