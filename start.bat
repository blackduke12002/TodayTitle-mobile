@echo off
echo ========================================
echo   TodayTitle Mobile - Streamlit Web App
echo ========================================
echo.

REM Check if DEEPSEEK_API_KEY is set
if not defined DEEPSEEK_API_KEY (
    echo [提示] 请设置 DEEPSEEK_API_KEY 环境变量
    echo.
    echo 临时设置方式（当前终端有效）：
    echo   set DEEPSEEK_API_KEY=你的api密钥
    echo.
    set /p API_KEY="或者请输入您的 DeepSeek API Key: "
    if not "%API_KEY%"=="" (
        set DEEPSEEK_API_KEY=%API_KEY%
        echo.
    )
)

echo [信息] 正在启动 Streamlit Web 应用...
echo.

streamlit run app.py

if errorlevel 1 (
    echo.
    echo [错误] 启动失败！
    echo.
    pause
)
