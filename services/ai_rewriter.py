"""DeepSeek AI calls: select + rewrite + evaluate for micro-headlines and articles."""
import json
import re
import requests
from typing import List, Dict

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_KEY = "sk-cc3b88858f184b4486c7cc29e125ccc9"
MODEL = "deepseek-chat"


class AIRewriteError(Exception):
    pass


def _call_deepseek(messages: List[Dict], temperature: float = 0.8,
                   max_tokens: int = 2048) -> str:
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    resp = requests.post(DEEPSEEK_URL, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    if "choices" not in data or not data["choices"]:
        raise AIRewriteError(f"AI返回异常: {json.dumps(data, ensure_ascii=False)[:200]}")

    return data["choices"][0]["message"]["content"]


def select_top3_for_viral(topics: List[Dict]) -> List[Dict]:
    """Given up to 5 topics, ask AI to pick the 3 most viral-worthy."""
    topic_list = "\n".join(
        f"{i + 1}. {t['name']} (热度: {t.get('hot', '未知')})"
        for i, t in enumerate(topics)
    )

    system_prompt = "你是一位资深的今日头条内容运营专家，擅长判断哪些热点话题最有可能引爆传播。"
    user_prompt = (
        f"以下是今日头条当前最热的{len(topics)}个话题：\n\n{topic_list}\n\n"
        "请从中选出最有可能引爆传播、最适合改写为职场主题微头条的3个话题。"
        "对每个选中话题，说明选择理由（一句话即可）。\n\n"
        "请严格按以下JSON格式返回，不要输出其他内容：\n"
        '[{"index": 1, "name": "话题名", "reason": "选择理由"}]'
    )

    content = _call_deepseek(
        [{"role": "system", "content": system_prompt},
         {"role": "user", "content": user_prompt}],
        temperature=0.6,
    )

    content = _strip_json(content)
    return json.loads(content)


def rewrite_to_micro_headline(topic_name: str) -> str:
    """Rewrite a hot topic into a workplace-themed viral micro-headline (100-300 chars)."""
    system_prompt = (
        "你是一位爆款微头条写手，擅长将热点新闻改写成职场主题的微头条。\n"
        "写作要求：\n"
        "1. 字数严格控制在100-300字之间\n"
        "2. 以职场人的视角切入，引发打工人共鸣\n"
        "3. 标题党风格，有冲击力，但内容有实质\n"
        "4. 风格：口语化、有态度、像真人分享\n"
        "5. 直接输出微头条正文，不要带任何前缀说明"
    )
    user_prompt = f"热点话题：{topic_name}\n\n请将上述热点改写为一篇职场主题的爆款微头条。"

    content = _call_deepseek(
        [{"role": "system", "content": system_prompt},
         {"role": "user", "content": user_prompt}],
        temperature=0.9,
    )
    return content.strip()


def evaluate_traffic_potential(micro_text: str) -> Dict[str, str]:
    """Evaluate a micro-headline. Returns {traffic_level, traffic_comment, originality}."""
    system_prompt = (
        "你是一位今日头条流量分析专家。请从以下维度评价这篇微头条：\n"
        "1. 标题吸引力\n"
        "2. 内容共鸣度\n"
        "3. 互动潜力\n"
        "4. 总体流量预估（高/中/低）\n"
        "5. 内容原创性（是否与网上常见内容雷同，是否存在洗稿嫌疑）\n\n"
        "请严格按以下JSON格式返回，不要输出其他内容：\n"
        '{"traffic_level": "高/中/低", "traffic_comment": "流量评价理由，30字内", '
        '"originality": "原创性评价，30字内"}'
    )
    user_prompt = f"请评价这篇微头条：\n\n{micro_text}"

    content = _call_deepseek(
        [{"role": "system", "content": system_prompt},
         {"role": "user", "content": user_prompt}],
        temperature=0.7,
    )

    content = _strip_json(content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "traffic_level": "未知",
            "traffic_comment": content[:60],
            "originality": "评价解析失败",
        }


def select_top3_for_articles(topics: List[Dict]) -> List[Dict]:
    """Pick 3 topics best suited for long-form Toutiao articles."""
    topic_list = "\n".join(
        f"{i + 1}. {t['name']} (热度: {t.get('hot', '未知')})"
        for i, t in enumerate(topics)
    )

    system_prompt = "你是一位今日头条号资深编辑，擅长判断哪些热点适合写成长文深度分析。"
    user_prompt = (
        f"以下是今日头条当前最热的{len(topics)}个话题：\n\n{topic_list}\n\n"
        "请从中选出最适合写成深度长文（800-1500字）的3个话题。"
        "选择标准：话题有足够深度可展开、能引发读者思考、适合职场人群阅读。"
        "对每个选中话题，说明选择理由（一句话即可）。\n\n"
        "请严格按以下JSON格式返回，不要输出其他内容：\n"
        '[{"index": 1, "name": "话题名", "reason": "选择理由"}]'
    )

    content = _call_deepseek(
        [{"role": "system", "content": system_prompt},
         {"role": "user", "content": user_prompt}],
        temperature=0.6,
    )

    content = _strip_json(content)
    return json.loads(content)


def rewrite_to_article(topic_name: str) -> Dict[str, str]:
    """Generate a Toutiao article. Returns {title, summary, body}."""
    system_prompt = (
        "你是一位今日头条号爆款写手，擅长将热点写成深度职场分析文章。\n"
        "文章要求：\n"
        "1. 标题15-30字，有冲击力，含关键词\n"
        "2. 导语50-100字，一句话钩住读者\n"
        "3. 正文800-1500字，结构清晰：现象引入 → 职场深度分析 → 观点总结\n"
        "4. 职场人视角，有态度有干货，引发共鸣和讨论\n"
        "5. 口语化但不失深度，像资深职场人在分享洞察\n\n"
        "请严格按以下JSON格式返回，不要输出其他内容：\n"
        '{"title": "文章标题", "summary": "导语一句话", '
        '"body": "正文内容（用\\\\n\\\\n分隔自然段落）"}'
    )
    user_prompt = f"热点话题：{topic_name}\n\n请将上述热点写成一篇今日头条爆款职场分析文章。"

    content = _call_deepseek(
        [{"role": "system", "content": system_prompt},
         {"role": "user", "content": user_prompt}],
        temperature=0.85,
        max_tokens=4096,
    )

    content = _strip_json(content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "title": "（标题解析失败）",
            "summary": "",
            "body": content[:1500],
        }


def evaluate_article(article_text: str) -> Dict[str, str]:
    """Evaluate an article. Returns {traffic_level, traffic_comment, originality}."""
    system_prompt = (
        "你是一位今日头条流量分析专家。请评价这篇文章：\n"
        "1. 标题吸引力\n"
        "2. 内容深度与价值\n"
        "3. 阅读完成率预估\n"
        "4. 总体流量预估（高/中/低）\n"
        "5. 内容原创性（是否与网上常见内容雷同，是否存在洗稿嫌疑）\n\n"
        "请严格按以下JSON格式返回，不要输出其他内容：\n"
        '{"traffic_level": "高/中/低", "traffic_comment": "评价理由，30字内", '
        '"originality": "原创性评价，30字内"}'
    )
    user_prompt = f"请评价这篇文章：\n\n{article_text}"

    content = _call_deepseek(
        [{"role": "system", "content": system_prompt},
         {"role": "user", "content": user_prompt}],
        temperature=0.7,
    )

    content = _strip_json(content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "traffic_level": "未知",
            "traffic_comment": content[:60],
            "originality": "评价解析失败",
        }


def _strip_json(text: str) -> str:
    """Strip markdown code fences from JSON response, extract JSON object/array."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:]) if len(lines) > 1 else text
        if text.endswith("```"):
            text = text[:-3].strip()
    if not text.startswith("[") and not text.startswith("{"):
        m = re.search(r"[\{\[].*[\}\]]", text, re.DOTALL)
        if m:
            text = m.group(0)
    return text
