# 快速构建 APK - 三种方案

由于本地没有 Android 构建环境，这里提供**三种更简单的方案**来获取 APK：

---

## 🚀 方案一：PWA Builder（最简单，推荐）

### 前置条件：先部署 Streamlit 后端

1. 启动 Streamlit 应用（需要公网可访问）：
   ```bash
   cd D:\Project\TodayTitle-mobile
   pip install -r requirements.txt
   set DEEPSEEK_API_KEY=你的_api_key
   streamlit run app.py --server.address 0.0.0.0
   ```

2. 使用内网穿透工具（如 ngrok）将本地服务暴露到公网：
   ```bash
   ngrok http 8501
   ```
   或者部署到云服务器（推荐）。

### 使用 PWA Builder 构建

1. 访问：https://www.pwabuilder.com/
2. 输入您部署后的 Streamlit 应用 URL
3. 点击 "Start" → 它会自动分析您的 PWA
4. 选择 "Android" 平台
5. 点击 "Build Package"
6. 下载生成的 APK 文件！

---

## 📱 方案二：Hermit - 将网站转为应用（无需构建）

这是最快的方案，不需要构建APK！

1. 在 Android 手机上安装 **Hermit** 应用：
   - Google Play: https://play.google.com/store/apps/details?id=com.chimbori.hermit
   
2. 打开 Hermit，输入您的 Streamlit 应用 URL
3. 点击 "创建轻应用"
4. 应用会自动添加到您的主屏幕，就像原生应用一样！

---

## 🛠️ 方案三：使用在线构建服务（不需要本地环境）

### 使用 AppGyver (SAP Build Apps)

1. 访问：https://www.appgyver.com/
2. 注册免费账户
3. 创建新项目
4. 添加 "Webview" 组件
5. 配置为您的 Streamlit 应用 URL
6. 构建 Android APK

### 使用 Web2App / Web2Apk

1. 访问：https://web2appmaker.com/ 或 https://web2apk.com/
2. 输入您的网站 URL
3. 配置应用名称、图标
4. 下载 APK

---

## 📋 部署后端到云服务器的快速方案

如果需要将 Streamlit 部署到公网，推荐：

### 选项 1：Streamlit Community Cloud（免费）
1. 上传代码到 GitHub
2. 访问 https://share.streamlit.io/
3. 连接 GitHub 仓库并部署

### 选项 2：Railway（免费额度）
1. 访问 https://railway.app/
2. 使用我们已创建的 `Dockerfile` 部署
3. 一键部署！

### 选项 3：Zeabur（简单）
1. 访问 https://zeabur.com/
2. 导入 GitHub 仓库
3. 自动部署

---

## 🎯 推荐流程总结

1. **第一步**：用 Streamlit Community Cloud 部署后端（免费）
2. **第二步**：用 PWA Builder 生成 APK（免费）
3. **第三步**：安装 APK 到手机

整个过程不需要写任何 Android 代码，也不需要配置复杂的构建环境！
