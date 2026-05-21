# TodayTitle Mobile - 今日爆款内容生成器（移动版）

基于 Streamlit 的 Web 应用，为移动设备优化。

## 功能特点

- 🎯 智能热点获取：实时获取今日头条热榜
- ✍️ 微头条生成：自动生成职场主题爆款微头条
- 📄 爆款文案：生成深度职场分析文章
- 🏆 流量评估：AI 评估内容潜力和原创性
- 📱 移动友好：为手机浏览器优化的界面

## 安装依赖

```bash
pip install -r requirements.txt
```

## 设置 API Key

设置环境变量：
```bash
# Windows
set DEEPSEEK_API_KEY=你的api密钥

# 或临时设置（仅当前终端有效）
$env:DEEPSEEK_API_KEY="你的api密钥"
```

## 运行应用

### Windows
```bash
# 方式1：使用启动脚本
start.bat

# 方式2：直接运行
streamlit run app.py
```

### 浏览器访问
应用启动后，会自动在浏览器打开，通常是：
http://localhost:8501

## 使用说明

1. 点击「获取今日热点」获取头条热榜
2. 在「微头条」标签页点击「生成微头条」
3. 在「爆款文案」标签页点击「生成爆款文案」
4. 点击「📋 复制」按钮复制生成的内容
5. 点击「清空」按钮可以重新开始

## 文件说明

- `app.py` - 主应用入口
- `services/hotspot_fetcher.py` - 热点获取服务
- `services/ai_rewriter.py` - AI 重写和评估服务
- `requirements.txt` - 依赖包列表
- `start.bat` - Windows 启动脚本
- `static/` - 静态资源（PWA 配置）

## 更新日志

### 最新更新
- ✅ 添加 Unicode 清理，解决 lone surrogate 问题
- ✅ 修复 Brotli 压缩解码问题，正确显示中文
- ✅ 添加 pyperclip 复制功能，带错误处理
- ✅ 修复清除后再次获取的状态管理
- ✅ API Key 从环境变量读取，更安全
