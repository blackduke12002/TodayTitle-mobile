@echo off
chcp 65001 >nul
echo ========================================
echo    今日爆款 - 快速启动工具
echo ========================================
echo.

echo [1/3] 检查 Python 环境...
python --version
if errorlevel 1 (
    echo ❌ 未找到 Python，请先安装 Python
    pause
    exit /b 1
)
echo ✅ Python 环境正常
echo.

echo [2/3] 检查依赖...
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
)
echo ✅ 依赖检查完成
echo.

echo [3/3] 启动应用...
echo.
echo ========================================
echo    应用启动中...
echo    请在浏览器中访问: http://localhost:8501
echo.
echo    要构建 APK，请阅读 QUICK_BUILD.md
echo ========================================
echo.

streamlit run app.py --server.address 0.0.0.0
pause
