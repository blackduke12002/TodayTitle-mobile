"""TodayTitle Mobile — Streamlit web app for mobile browsers."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from services.hotspot_fetcher import fetch_hot_topics, HotspotFetchError
from services.ai_rewriter import (
    select_top3_for_viral, rewrite_to_micro_headline,
    evaluate_traffic_potential,
    select_top3_for_articles, rewrite_to_article,
    evaluate_article, AIRewriteError,
    rewrite_micro_multi_angle, rewrite_article_multi_angle,
    MICRO_ANGLES, ARTICLE_ANGLES,
)
import pyperclip


def _get_secret_or_env(key: str, default: str = "") -> str:
    """Try st.secrets first (Streamlit Cloud), then env var, then default."""
    try:
        return st.secrets.get(key, os.environ.get(key, default))
    except Exception:
        return os.environ.get(key, default)

st.set_page_config(
    page_title="今日爆款内容生成器",
    page_icon="📰",
    layout="centered",
)

st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 1.1rem;
        font-weight: bold;
        border-radius: 12px;
    }
    .copy-btn > button {
        width: auto;
        height: 2.2rem;
        font-size: 0.85rem;
        font-weight: normal;
        border-radius: 8px;
    }
    .result-card {
        border: 1px solid #444;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        background-color: #1e1e1e;
    }
    .eval-box {
        border-left: 4px solid #4A90D9;
        padding: 10px 14px;
        margin: 10px 0;
        font-size: 0.9rem;
        border-radius: 8px;
        background-color: #1a1a2e;
        color: #ffffff;
        line-height: 1.6;
    }
    .eval-box-article {
        border-left: 4px solid #e67e22;
        padding: 10px 14px;
        margin: 10px 0;
        font-size: 0.9rem;
        border-radius: 8px;
        background-color: #1a1a2e;
        color: #ffffff;
        line-height: 1.6;
    }
    .hot-item {
        padding: 4px 0;
        font-size: 0.9rem;
    }
    .char-count {
        color: #888;
        font-size: 0.8rem;
    }
    .title-text {
        font-size: 1.3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="title-text">📰 今日爆款内容生成器</p>', unsafe_allow_html=True)

# ── AI Provider Selection ──
st.sidebar.markdown("### ⚙️ AI 设置")

ai_provider = st.sidebar.selectbox(
    "选择 AI 提供商",
    ["本地模式（免费）", "Gemini（免费额度）", "DeepSeek", "HuggingFace"],
    index=0,
    help="本地模式无需 API Key，直接使用模板生成"
)

if ai_provider == "本地模式（免费）":
    os.environ["AI_PROVIDER"] = "local"
    st.sidebar.success("使用本地模式，无需 API Key")
elif ai_provider == "Gemini（免费额度）":
    os.environ["AI_PROVIDER"] = "gemini"
    prefill_key = _get_secret_or_env("GOOGLE_API_KEY")
    gemini_key = st.sidebar.text_input(
        "Google API Key",
        type="password",
        value=prefill_key,
        placeholder="请输入 Google API Key",
        help="获取地址: https://makersuite.google.com/"
    )
    if gemini_key:
        os.environ["GOOGLE_API_KEY"] = gemini_key
        st.sidebar.success("Gemini API Key 已设置")
    else:
        st.sidebar.warning("请设置 Google API Key")
elif ai_provider == "DeepSeek":
    os.environ["AI_PROVIDER"] = "deepseek"

    # ── Base URL ──
    default_url = _get_secret_or_env("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1/chat/completions")
    base_url = st.sidebar.text_input(
        "Base URL",
        value=default_url,
        placeholder="https://api.deepseek.com/v1/chat/completions",
        help="API 端点地址，支持任何 OpenAI 兼容接口",
        key="deepseek_base_url",
    )
    if base_url:
        os.environ["DEEPSEEK_BASE_URL"] = base_url

    # ── Model ──
    default_model = _get_secret_or_env("DEEPSEEK_MODEL", "deepseek-chat")
    model = st.sidebar.text_input(
        "Model",
        value=default_model,
        placeholder="deepseek-chat",
        help="模型名称，如 deepseek-chat、gpt-4o、glm-4 等",
        key="deepseek_model",
    )
    if model:
        os.environ["DEEPSEEK_MODEL"] = model

    # ── API Key ──
    prefill_key = _get_secret_or_env("DEEPSEEK_API_KEY")
    deepseek_key = st.sidebar.text_input(
        "DeepSeek API Key",
        type="password",
        value=prefill_key,
        placeholder="请输入 DeepSeek API Key",
        help="获取地址: https://platform.deepseek.com/",
        key="deepseek_key",
    )
    if deepseek_key:
        os.environ["DEEPSEEK_API_KEY"] = deepseek_key

    # ── Key status ──
    col_status, col_test = st.sidebar.columns([3, 1])
    if deepseek_key:
        col_status.success("Key 已设置")
    else:
        col_status.warning("请设置 API Key")

    if col_test.button("测试", key="test_deepseek", use_container_width=True):
        if not deepseek_key:
            st.sidebar.error("请先填写 API Key")
        else:
            with st.sidebar:
                with st.spinner("测试连接..."):
                    try:
                        import requests as _r
                        resp = _r.post(
                            base_url or "https://api.deepseek.com/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {deepseek_key}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": model or "deepseek-chat",
                                "messages": [{"role": "user", "content": "hi"}],
                                "max_tokens": 5,
                            },
                            timeout=30,
                        )
                        if resp.status_code == 200:
                            st.success("连接成功！API Key 有效")
                        elif resp.status_code == 401:
                            st.error("API Key 无效(401)")
                        elif resp.status_code == 402:
                            st.error("余额不足(402)")
                        elif resp.status_code == 429:
                            st.error("请求频率超限(429)")
                        else:
                            st.error(f"请求失败({resp.status_code})")
                    except Exception as ex:
                        st.error(f"网络请求失败: {str(ex)}")
elif ai_provider == "HuggingFace":
    os.environ["AI_PROVIDER"] = "huggingface"
    prefill_key = _get_secret_or_env("HUGGINGFACE_API_KEY")
    hf_key = st.sidebar.text_input(
        "HuggingFace API Key",
        type="password",
        value=prefill_key,
        placeholder="请输入 HuggingFace API Key",
        help="获取地址: https://huggingface.co/settings/tokens"
    )
    if hf_key:
        os.environ["HUGGINGFACE_API_KEY"] = hf_key
        st.sidebar.success("HuggingFace API Key 已设置")
    else:
        st.sidebar.warning("请设置 HuggingFace API Key")

# ── Session state init ──
for key, default in {
    "hotspots": [], "hotspots_fetched": False,
    "micro_0": "", "micro_1": "", "micro_2": "",
    "micro_eval_0": {}, "micro_eval_1": {}, "micro_eval_2": {},
    "article_0": {}, "article_1": {}, "article_2": {},
    "article_eval_0": {}, "article_eval_1": {}, "article_eval_2": {},
    "micro_generated": False, "article_generated": False,
    "selected_micro": [], "selected_article": [],
    "source_mode": "fetched", "custom_hotspots": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Hotspot section ──
st.markdown("### 🔥 热点获取")
col1, col2 = st.columns([3, 1])
with col1:
    fetch_clicked = st.button("获取今日热点", type="primary", use_container_width=True)
with col2:
    clear_clicked = st.button("清空", use_container_width=True)

if fetch_clicked:
    with st.spinner("正在获取今日头条热搜..."):
        try:
            topics = fetch_hot_topics(limit=5)
            st.session_state.hotspots = topics
            st.session_state.hotspots_fetched = True
            st.success(f"获取成功！{len(topics)} 个热点")
        except HotspotFetchError as e:
            st.error(f"获取失败: {e}")

if clear_clicked:
    st.session_state.hotspots = []
    st.session_state.hotspots_fetched = False

if st.session_state.hotspots_fetched:
    st.markdown("**今日头条热榜 Top 5:**")
    for i, t in enumerate(st.session_state.hotspots):
        hot_text = f" ({t['hot']})" if t.get('hot') else ""
        st.markdown(f'<div class="hot-item">{i + 1}. {t["name"]}<small style="color:#888;">{hot_text}</small></div>',
                    unsafe_allow_html=True)

# ── Source mode & custom hotspots ──
source_mode = st.radio(
    "内容来源",
    ["获取的热点", "自定义热点"],
    horizontal=True,
    key="source_mode_radio",
    index=0 if st.session_state.source_mode == "fetched" else 1,
)
st.session_state.source_mode = "fetched" if source_mode == "获取的热点" else "custom"

if st.session_state.source_mode == "custom":
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        custom_input = st.text_input(
            "输入你想追的热点话题",
            placeholder="输入热点话题，点击添加...",
            key="custom_input",
            label_visibility="collapsed",
        )
    with col_btn:
        if st.button("添加", key="add_custom", use_container_width=True):
            topic = custom_input.strip()
            if topic:
                st.session_state.custom_hotspots.append({
                    "name": topic, "hot": "自定义",
                })
                st.rerun()

    if st.session_state.custom_hotspots:
        for i, t in enumerate(st.session_state.custom_hotspots):
            col_name, col_del = st.columns([5, 1])
            with col_name:
                st.markdown(f'{i + 1}. {t["name"]} <small style="color:#888;">(自定义)</small>',
                            unsafe_allow_html=True)
            with col_del:
                if st.button("删除", key=f"del_custom_{i}", use_container_width=True):
                    st.session_state.custom_hotspots.pop(i)
                    st.rerun()
    else:
        st.info("添加自定义热点话题后，AI 将从3个不同角度生成内容")

st.markdown("---")

# ── Tabs ──
tab1, tab2 = st.tabs(["📝 微头条", "📄 爆款文案"])

# ========== TAB 1: 微头条 ==========
with tab1:
    has_source = (
        st.session_state.hotspots_fetched and st.session_state.source_mode == "fetched"
    ) or (
        len(st.session_state.custom_hotspots) > 0 and st.session_state.source_mode == "custom"
    )
    if has_source:
        gen_micro = st.button("生成微头条", type="primary", key="gen_micro")
    else:
        if st.session_state.source_mode == "custom":
            st.info("请先在上方添加自定义热点")
        else:
            st.info("请先在上方获取今日热点")
        gen_micro = False

    if gen_micro:
        st.session_state.micro_generated = False
        for i in range(3):
            st.session_state[f"micro_{i}"] = ""
            st.session_state[f"micro_eval_{i}"] = {}

        is_custom = st.session_state.source_mode == "custom"

        with st.spinner("正在AI多角度改写..." if is_custom else "正在AI筛选与改写..."):
            try:
                if is_custom:
                    topic_name = st.session_state.custom_hotspots[0]["name"]
                    results = rewrite_micro_multi_angle(topic_name)
                    st.session_state.selected_micro = [
                        {"index": i + 1, "name": topic_name, "reason": MICRO_ANGLES[i]}
                        for i in range(3)
                    ]
                    for i, micro_text in enumerate(results):
                        st.session_state[f"micro_{i}"] = micro_text
                        try:
                            eval_data = evaluate_traffic_potential(micro_text)
                            st.session_state[f"micro_eval_{i}"] = eval_data
                        except Exception:
                            st.session_state[f"micro_eval_{i}"] = {
                                "traffic_level": "未知",
                                "traffic_comment": "评价暂时无法获取",
                                "originality": "评价暂时无法获取",
                            }
                else:
                    topics = st.session_state.hotspots
                    selected = select_top3_for_viral(topics)
                    st.session_state.selected_micro = selected

                    for i, item in enumerate(selected):
                        status_text = st.empty()
                        status_text.write(f"⏳ 正在生成微头条 {i + 1}/3...")

                        micro_text = rewrite_to_micro_headline(item["name"])
                        st.session_state[f"micro_{i}"] = micro_text

                        try:
                            eval_data = evaluate_traffic_potential(micro_text)
                            st.session_state[f"micro_eval_{i}"] = eval_data
                        except Exception:
                            st.session_state[f"micro_eval_{i}"] = {
                                "traffic_level": "未知",
                                "traffic_comment": "评价暂时无法获取",
                                "originality": "评价暂时无法获取",
                            }
                        status_text.empty()

                st.session_state.micro_generated = True
                st.success("生成完成！")
            except Exception as e:
                st.error(f"生成失败: {e}")

    if st.session_state.micro_generated:
        for i in range(3):
            text = st.session_state.get(f"micro_{i}", "")
            if not text:
                continue

            char_count = len(text.replace("\n", "").replace(" ", ""))
            eval_data = st.session_state.get(f"micro_eval_{i}", {})

            # Angle label for custom mode
            angle_label = ""
            if st.session_state.source_mode == "custom" and i < len(MICRO_ANGLES):
                angle_label = f" — {MICRO_ANGLES[i].split('：')[0]}"

            with st.container():
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown(f"**爆款微头条 #{i + 1}{angle_label}** <span class='char-count'>({char_count}字)</span>",
                            unsafe_allow_html=True)

                st.code(text, language=None)

                if eval_data:
                    tl = eval_data.get("traffic_level", "未知")
                    tc = eval_data.get("traffic_comment", "")
                    og = eval_data.get("originality", "")

                    st.markdown(f"""<div class="eval-box">
                        <b style="color:#64B5F6;">📊 流量预估：</b><b style="color:#FFD54F;">{tl}</b> — <span style="color:#E0E0E0;">{tc}</span><br>
                        <b style="color:#FFB74D;">✏️ 原创性：</b><span style="color:#E0E0E0;">{og}</span>
                    </div>""", unsafe_allow_html=True)

                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    if st.button(f"📋 复制", key=f"copy_micro_{i}"):
                        try:
                            pyperclip.copy(text)
                            st.toast("已复制到剪贴板", icon="✅")
                        except Exception:
                            st.toast("复制失败，请手动复制", icon="❌")
                with col_btn2:
                    if st.button(f"🔄 重新生成", key=f"regen_micro_{i}"):
                        if i < len(st.session_state.get("selected_micro", [])):
                            topic = st.session_state.selected_micro[i]["name"]
                            with st.spinner("重新生成中..."):
                                new_text = rewrite_to_micro_headline(topic)
                                st.session_state[f"micro_{i}"] = new_text
                                try:
                                    st.session_state[f"micro_eval_{i}"] = evaluate_traffic_potential(new_text)
                                except Exception:
                                    pass
                            st.rerun()
                with col_btn3:
                    if st.button(f"🗑️ 清空", key=f"clear_micro_{i}"):
                        st.session_state[f"micro_{i}"] = ""
                        st.session_state[f"micro_eval_{i}"] = {}
                        st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)

# ========== TAB 2: 爆款文案 ==========
with tab2:
    has_source = (
        st.session_state.hotspots_fetched and st.session_state.source_mode == "fetched"
    ) or (
        len(st.session_state.custom_hotspots) > 0 and st.session_state.source_mode == "custom"
    )
    if has_source:
        gen_article = st.button("生成爆款文案", type="primary", key="gen_article")
    else:
        if st.session_state.source_mode == "custom":
            st.info("请先在上方添加自定义热点")
        else:
            st.info("请先在上方获取今日热点")
        gen_article = False

    if gen_article:
        st.session_state.article_generated = False
        for i in range(3):
            st.session_state[f"article_{i}"] = {}
            st.session_state[f"article_eval_{i}"] = {}

        is_custom = st.session_state.source_mode == "custom"

        with st.spinner("正在AI多角度生成文章..." if is_custom else "正在AI筛选与生成文章..."):
            try:
                if is_custom:
                    topic_name = st.session_state.custom_hotspots[0]["name"]
                    results = rewrite_article_multi_angle(topic_name)
                    st.session_state.selected_article = [
                        {"index": i + 1, "name": topic_name, "reason": ARTICLE_ANGLES[i]}
                        for i in range(3)
                    ]
                    for i, article in enumerate(results):
                        st.session_state[f"article_{i}"] = article
                        full_text = f"{article.get('title', '')}\n{article.get('summary', '')}\n{article.get('body', '')}"
                        try:
                            eval_data = evaluate_article(full_text)
                            st.session_state[f"article_eval_{i}"] = eval_data
                        except Exception:
                            st.session_state[f"article_eval_{i}"] = {
                                "traffic_level": "未知",
                                "traffic_comment": "评价暂时无法获取",
                                "originality": "评价暂时无法获取",
                            }
                else:
                    topics = st.session_state.hotspots
                    selected = select_top3_for_articles(topics)
                    st.session_state.selected_article = selected

                    for i, item in enumerate(selected):
                        status_text = st.empty()
                        status_text.write(f"⏳ 正在生成文章 {i + 1}/3...")

                        article = rewrite_to_article(item["name"])
                        st.session_state[f"article_{i}"] = article

                        full_text = f"{article.get('title', '')}\n{article.get('summary', '')}\n{article.get('body', '')}"
                        try:
                            eval_data = evaluate_article(full_text)
                            st.session_state[f"article_eval_{i}"] = eval_data
                        except Exception:
                            st.session_state[f"article_eval_{i}"] = {
                                "traffic_level": "未知",
                                "traffic_comment": "评价暂时无法获取",
                                "originality": "评价暂时无法获取",
                            }
                        status_text.empty()

                st.session_state.article_generated = True
                st.success("文章生成完成！")
            except Exception as e:
                st.error(f"生成失败: {e}")

    if st.session_state.article_generated:
        for i in range(3):
            article = st.session_state.get(f"article_{i}", {})
            if not article:
                continue

            title = article.get("title", "")
            summary = article.get("summary", "")
            body = article.get("body", "")
            full_text = f"{title}\n\n{summary}\n\n{body}"
            char_count = len(full_text.replace("\n", "").replace(" ", ""))
            eval_data = st.session_state.get(f"article_eval_{i}", {})

            # Angle label for custom mode
            angle_label = ""
            if st.session_state.source_mode == "custom" and i < len(ARTICLE_ANGLES):
                angle_label = f" — {ARTICLE_ANGLES[i].split('：')[0]}"

            with st.container():
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown(f"**爆款文案 #{i + 1}{angle_label}** <span class='char-count'>({char_count}字)</span>",
                            unsafe_allow_html=True)

                formatted = f"【标题】\n{title}\n\n【导语】\n{summary}\n\n【正文】\n{body}"
                st.code(formatted, language=None)

                if eval_data:
                    tl = eval_data.get("traffic_level", "未知")
                    tc = eval_data.get("traffic_comment", "")
                    og = eval_data.get("originality", "")

                    st.markdown(f"""<div class="eval-box-article">
                        <b style="color:#FFA726;">📊 流量预估：</b><b style="color:#FFD54F;">{tl}</b> — <span style="color:#E0E0E0;">{tc}</span><br>
                        <b style="color:#FFB74D;">✏️ 原创性：</b><span style="color:#E0E0E0;">{og}</span>
                    </div>""", unsafe_allow_html=True)

                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    if st.button(f"📋 复制", key=f"copy_article_{i}"):
                        try:
                            pyperclip.copy(formatted)
                            st.toast("已复制到剪贴板", icon="✅")
                        except Exception:
                            st.toast("复制失败，请手动复制", icon="❌")
                with col_btn2:
                    if st.button(f"🔄 重新生成", key=f"regen_article_{i}"):
                        if i < len(st.session_state.get("selected_article", [])):
                            topic = st.session_state.selected_article[i]["name"]
                            with st.spinner("重新生成中..."):
                                new_article = rewrite_to_article(topic)
                                st.session_state[f"article_{i}"] = new_article
                                ft = f"{new_article.get('title', '')}\n{new_article.get('summary', '')}\n{new_article.get('body', '')}"
                                try:
                                    st.session_state[f"article_eval_{i}"] = evaluate_article(ft)
                                except Exception:
                                    pass
                            st.rerun()
                with col_btn3:
                    if st.button(f"🗑️ 清空", key=f"clear_article_{i}"):
                        st.session_state[f"article_{i}"] = {}
                        st.session_state[f"article_eval_{i}"] = {}
                        st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ──
st.markdown("---")
st.caption("📱 今日爆款内容生成器 · 移动版 · 添加到桌面可像 App 一样使用")
