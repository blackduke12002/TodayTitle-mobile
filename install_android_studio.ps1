# Android Studio installation script
param(
    [string]$InstallPath = "C:\Program Files\Android\Android Studio",
    [string]$SdkPath = "$env:USERPROFILE\AppData\Local\Android\Sdk"
)

Write-Host "=== Android Studio Installer ==="
Write-Host ""

$downloadUrl = "https://dl.google.com/dl/android/studio/install/2024.3.2.15/android-studio-2024.3.2.15-windows.exe"
$installerPath = "$env:TEMP\android-studio-installer.exe"

Write-Host "[1/4] Downloading Android Studio..."
Write-Host "URL: $downloadUrl"
try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing
    Write-Host "Download completed successfully"
} catch {
    Write-Host "Download failed: $_"
    exit 1
}

Write-Host "[2/4] Installing Android Studio..."
Write-Host "Path: $InstallPath"
try {
    $process = Start-Process -FilePath $installerPath -ArgumentList "/S /D=`"$InstallPath`"" -Wait -PassThru -NoNewWindow
    if ($process.ExitCode -eq 0) {
        Write-Host "Installation completed successfully"
    } else {
        Write-Host "Installation failed with code: $($process.ExitCode)"
        exit 1
    }
} catch {
    Write-Host "Installation error: $_"
    exit 1
}

Write-Host "[3/4] Setting environment variables..."
try {
    [Environment]::SetEnvironmentVariable("ANDROID_HOME", $SdkPath, "User")
    [Environment]::SetEnvironmentVariable("ANDROID_SDK_ROOT", $SdkPath, "User")
    Write-Host "Environment variables set successfully"
} catch {
    Write-Host "Failed to set environment variables: $_"
}

Write-Host "[4/4] Creating SDK directory..."
try {
    New-Item -ItemType Directory -Path $SdkPath -Force | Out-Null
    Write-Host "SDK directory created: $SdkPath"
} catch {
    Write-Host "Failed to create SDK directory: $_"
}

Write-Host ""
Write-Host "=== Installation Complete ==="
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Start Android Studio from Start Menu"
Write-Host "2. Complete initial setup (select standard settings)"
Write-Host "3. Open project: D:\Project\TodayTitle-mobile\android\"
Write-Host "4. Click Build -> Build APK(s)"
