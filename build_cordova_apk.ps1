# Cordova APK 构建脚本
param(
    [string]$AppName = "TodayTitle",
    [string]$AppId = "com.todaytitle.app",
    [string]$AppVersion = "1.0.0"
)

Write-Host "=== 初始化 Cordova 项目 ==="

# 检查 Node.js
try {
    node --version | Out-Null
} catch {
    Write-Host "❌ 请先安装 Node.js" -ForegroundColor Red
    exit 1
}

# 安装 Cordova
Write-Host "[1/5] 安装 Cordova..."
npm install -g cordova

# 创建项目目录
Write-Host "[2/5] 创建 Cordova 项目..."
Remove-Item -Recurse -Force "cordova-app" -ErrorAction SilentlyContinue
cordova create cordova-app $AppId $AppName

cd cordova-app

# 添加 Android 平台
Write-Host "[3/5] 添加 Android 平台..."
cordova platform add android

# 创建应用内容
Write-Host "[4/5] 创建应用内容..."
$indexContent = @"
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>$AppName</title>
    <style>
        body { margin: 0; padding: 0; height: 100vh; overflow: hidden; }
        iframe { width: 100%; height: 100%; border: none; }
    </style>
</head>
<body>
    <iframe src="http://localhost:8501"></iframe>
</body>
</html>
"@

Set-Content -Path "www/index.html" -Value $indexContent

# 构建 APK
Write-Host "[5/5] 构建 APK..."
cordova build android --debug

Write-Host ""
Write-Host "=== 构建完成 ==="
Write-Host "APK 位置: cordova-app/platforms/android/app/build/outputs/apk/debug/app-debug.apk"
