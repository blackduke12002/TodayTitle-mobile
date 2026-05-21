# 今日爆款 - Android APK 构建指南

## 项目结构

```
TodayTitle-mobile/
├── app.py                  # Streamlit 后端应用
├── android/                # Android WebView 应用
│   ├── app/
│   │   ├── src/
│   │   │   └── main/
│   │   │       ├── java/com/todaytitle/app/MainActivity.kt
│   │   │       ├── res/
│   │   │       └── AndroidManifest.xml
│   │   └── build.gradle
│   ├── build.gradle
│   ├── settings.gradle
│   └── gradle.properties
├── deploy_config.py        # 部署配置工具
└── requirements.txt        # Python 依赖
```

## 第一步：部署 Streamlit 后端

### 方式一：本地运行（用于测试）

1. 安装 Python 依赖：
```bash
pip install -r requirements.txt
```

2. 设置环境变量：
```bash
# Windows
set DEEPSEEK_API_KEY=你的_api_key

# Linux/Mac
export DEEPSEEK_API_KEY=你的_api_key
```

3. 运行应用：
```bash
streamlit run app.py
```

### 方式二：Docker 部署（推荐用于生产）

1. 运行配置工具生成部署文件：
```bash
python deploy_config.py
```

2. 复制环境变量文件：
```bash
cp .env.example .env
# 编辑 .env 填入你的 DEEPSEEK_API_KEY
```

3. 启动服务：
```bash
docker-compose up -d
```

4. 服务将在 `http://localhost:8501` 运行

## 第二步：构建 Android APK

### 前置要求

- Android Studio Hedgehog (2023.1.1) 或更高版本
- JDK 17 或更高版本
- Android SDK (API 34)

### 步骤

1. **打开 Android 项目**
   - 启动 Android Studio
   - 选择 "Open an Existing Project"
   - 选择 `TodayTitle-mobile/android/` 目录

2. **配置服务器地址**
   - 打开 `android/app/src/main/java/com/todaytitle/app/MainActivity.kt`
   - 修改 `BASE_URL` 为你的后端服务器地址：
     ```kotlin
     // 如果是本地测试（模拟器）：
     private val BASE_URL = "http://10.0.2.2:8501"
     
     // 如果是局域网测试（真机）：
     private val BASE_URL = "http://你的电脑IP:8501"
     
     // 如果是公网服务器：
     private val BASE_URL = "https://your-domain.com"
     ```

3. **同步 Gradle**
   - 等待 Android Studio 自动同步 Gradle
   - 或点击 "Sync Project with Gradle Files" 按钮

4. **生成签名密钥（用于发布版 APK）**
   ```bash
   # 在 android/ 目录下执行
   keytool -genkey -v -keystore release-key.keystore -alias release -keyalg RSA -keysize 2048 -validity 10000
   ```

5. **配置签名**
   - 在 `android/app/build.gradle` 中添加签名配置（可选）

6. **构建 APK**
   
   **Debug APK（测试用）：**
   - 菜单栏：Build → Build Bundle(s) / APK(s) → Build APK(s)
   - 或使用命令行：
     ```bash
     cd android
     ./gradlew assembleDebug
     ```
   - APK 位置：`android/app/build/outputs/apk/debug/app-debug.apk`

   **Release APK（发布用）：**
   - 菜单栏：Build → Generate Signed Bundle / APK
   - 选择 "APK"
   - 选择密钥库文件并输入密码
   - 选择 "release" 构建变体
   - 或使用命令行：
     ```bash
     cd android
     ./gradlew assembleRelease
     ```
   - APK 位置：`android/app/build/outputs/apk/release/app-release.apk`

## 第三步：安装 APK 到手机

1. **启用开发者选项**
   - 进入手机设置 → 关于手机
   - 连续点击"版本号"7次
   - 返回设置，找到"开发者选项"

2. **启用 USB 调试**
   - 在开发者选项中启用"USB 调试"

3. **连接手机**
   - 使用 USB 数据线连接手机和电脑
   - 在手机上允许 USB 调试

4. **安装 APK**
   ```bash
   # 使用 adb 安装
   adb install app-debug.apk
   ```
   - 或直接将 APK 文件复制到手机并点击安装

## 注意事项

### 网络配置

- 如果使用公网服务器，建议使用 HTTPS
- 如果使用 HTTP，已在 `AndroidManifest.xml` 中设置 `android:usesCleartextTraffic="true"`

### 模拟器测试

- Android 模拟器访问主机 localhost 使用 `10.0.2.2`
- Genymotion 模拟器使用 `10.0.3.2`

### 真机局域网测试

- 确保手机和电脑在同一局域网
- 关闭电脑防火墙或允许 8501 端口
- 使用电脑的局域网 IP 地址

### 应用图标

- 当前使用默认图标
- 可替换 `android/app/src/main/res/mipmap-*/` 下的图标文件

## 常见问题

### Q: 构建时提示 Gradle 版本错误？
A: 检查 `gradle/wrapper/gradle-wrapper.properties` 中的 Gradle 版本，或使用 Android Studio 推荐的版本。

### Q: WebView 无法加载页面？
A: 
1. 检查后端服务是否正常运行
2. 确认服务器地址配置正确
3. 检查网络连接和防火墙设置

### Q: 如何修改应用名称？
A: 修改 `android/app/src/main/res/values/strings.xml` 中的 `app_name`

### Q: 如何修改包名？
A: 
1. 修改 `build.gradle` 中的 `applicationId`
2. 修改 `AndroidManifest.xml` 中的 `package`
3. 重构 Kotlin 文件的包名

## 技术支持

如有问题，请检查：
1. Streamlit 后端日志
2. Android Logcat 日志
3. 网络连接状态
