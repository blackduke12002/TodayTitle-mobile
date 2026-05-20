# TodayTitle Mobile

AI驱动的今日头条爆款内容生成器，Streamlit 移动版 + TWA 打包为 APK。

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 部署到 Streamlit Cloud

1. Push 到 GitHub
2. 在 [share.streamlit.io](https://share.streamlit.io) 连接此仓库
3. 主文件路径选择 `app.py`

## 打包为 APK

部署后，使用 [pwabuilder.com](https://pwabuilder.com) 输入 Streamlit Cloud URL，自动生成 Android APK。
