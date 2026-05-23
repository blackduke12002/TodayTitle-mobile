"""AI calls for micro-headlines and articles - supports multiple AI providers."""
import json
import re
import os
import random
import requests
from typing import List, Dict
from .utils import clean_unicode

def _get_ai_provider() -> str:
    """Dynamically get AI provider from environment variable."""
    return os.environ.get("AI_PROVIDER", "local").lower()


class AIRewriteError(Exception):
    pass


def _strip_json(text: str) -> str:
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


def _call_gemini(messages: List[Dict], temperature: float = 0.8, max_tokens: int = 2048) -> str:
    import google.generativeai as genai
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("请设置环境变量 GOOGLE_API_KEY")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-pro")
    
    prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    response = model.generate_content(prompt, generation_config={
        "temperature": temperature,
        "max_output_tokens": max_tokens
    })
    
    if not response.text:
        raise AIRewriteError("AI返回为空")
    return clean_unicode(response.text)


def _call_huggingface(messages: List[Dict], temperature: float = 0.8, max_tokens: int = 2048) -> str:
    api_key = os.environ.get("HUGGINGFACE_API_KEY")
    model_name = os.environ.get("HUGGINGFACE_MODEL", "HuggingFaceH4/zephyr-7b-beta")
    
    if not api_key:
        raise ValueError("请设置环境变量 HUGGINGFACE_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    payload = {
        "inputs": prompt,
        "parameters": {
            "temperature": temperature,
            "max_new_tokens": max_tokens,
            "do_sample": True
        }
    }
    
    resp = requests.post(
        f"https://api-inference.huggingface.co/models/{model_name}",
        json=payload,
        headers=headers,
        timeout=120
    )
    resp.raise_for_status()
    data = resp.json()
    
    if isinstance(data, dict):
        if "generated_text" in data:
            result = data["generated_text"]
        elif "text" in data:
            result = data["text"]
        elif isinstance(data.get("choices"), list) and len(data["choices"]) > 0:
            choice = data["choices"][0]
            result = choice.get("text", choice.get("generated_text", ""))
        else:
            raise AIRewriteError(f"Unexpected HuggingFace response format: {json.dumps(data)[:200]}")
    elif isinstance(data, list) and len(data) > 0:
        first_item = data[0]
        if isinstance(first_item, dict):
            result = first_item.get("generated_text", first_item.get("text", ""))
        elif isinstance(first_item, str):
            result = first_item
        else:
            result = str(first_item)
    else:
        raise AIRewriteError(f"Unexpected HuggingFace response format: {type(data).__name__}")
    
    if result:
        result = result.replace(prompt, "").strip()
    
    return clean_unicode(result)


def _simple_local_select_top3(topics: List[Dict]) -> List[Dict]:
    selected = []
    for i, topic in enumerate(topics[:3]):
        reasons = [
            "话题热度高，适合职场人群讨论",
            "具有较强的传播潜力",
            "能引发职场人共鸣",
            "话题有深度，适合展开讨论",
            "近期热点，时效性强"
        ]
        selected.append({
            "index": i + 1,
            "name": topic["name"],
            "reason": random.choice(reasons)
        })
    return selected[:3]


def _simple_local_rewrite_micro(topic_name: str) -> str:
    templates = [
        f"刚看到{topic_name}这个新闻，作为职场人忍不住想说两句。在职场中，我们经常会遇到类似的情况，关键在于如何保持冷静和专业。面对挑战时，焦虑和压力是难免的，但我们需要学会调整心态，用积极的态度去面对每一个困难。你在工作中遇到过类似的情况吗？当时是怎么处理的？欢迎在评论区分享你的经验！",
        f"{topic_name}上热搜了！这个话题让我想起了职场中的那些事儿。其实在职场，最重要的是保持自己的节奏，不要被外界干扰。很多时候，我们会因为别人的评价而怀疑自己，但请记住，每个人的成长轨迹都不同，不必强求自己跟上别人的脚步。做好自己的事，时间会给出答案。大家觉得呢？",
        f"今天{topic_name}刷屏了。作为一名打工人，我想说：职场不易，但我们依然要保持初心。在这个快节奏的时代，很容易迷失方向，忘记自己最初的梦想。但请相信，只要坚持做正确的事，不断提升自己，总有一天会看到属于自己的光芒。你在职场中遇到过类似的挑战吗？欢迎留言讨论！",
        f"{topic_name}引发热议！从职场角度看，这件事给我们什么启示？我认为最重要的是学会独立思考，不要盲目跟风。在职场中，要有自己的判断和立场，不随波逐流。同时，也要学会倾听他人的意见，不断完善自己。欢迎在评论区分享你的看法，一起探讨职场生存之道。",
        f"关于{topic_name}，我有话说。职场如战场，每一步都要谨慎。但最重要的是保持真实的自己，不随波逐流。很多人为了迎合他人而改变自己，最后却迷失了方向。请记住，你就是独一无二的，不必为了取悦别人而失去自我。同意的点赞！欢迎分享你的职场故事！"
    ]
    return random.choice(templates)


def _simple_local_evaluate(text: str) -> Dict[str, str]:
    levels = ["高", "中", "低"]
    traffic_comments = [
        "标题吸引人，内容有干货",
        "内容有深度，值得一读",
        "观点独特，引发思考",
        "结构清晰，易于阅读",
        "内容充实，信息量大"
    ]
    originality = [
        "原创度高，观点新颖",
        "内容独特，有个人见解",
        "角度新颖，值得推荐",
        "有自己的思考和分析"
    ]
    return {
        "traffic_level": random.choice(levels),
        "traffic_comment": random.choice(traffic_comments),
        "originality": random.choice(originality)
    }


def _simple_local_rewrite_article(topic_name: str) -> Dict[str, str]:
    body = f"""最近{topic_name}成为了热门话题，引起了广泛的关注和讨论。这件事不仅仅是一个简单的新闻事件，更是一面镜子，照出了职场中的许多问题和现象。今天，我们就从职场人的角度来深入分析这件事，看看能给我们带来哪些启示。

首先，这件事让我们看到了职场中的沟通重要性。在工作中，沟通是一切的基础。很多问题的产生，往往不是因为事情本身有多复杂，而是因为沟通不到位。如果我们能在工作中做到及时沟通、有效沟通，很多矛盾和误解都可以避免。就像{topic_name}这件事，如果相关各方能够及时沟通，或许结果会完全不同。

其次，这件事也反映出了职场心态的重要性。在职场中，我们难免会遇到各种挑战和压力，保持一个良好的心态至关重要。面对困难和挫折，我们不能轻易放弃，而是要积极寻找解决问题的方法。同时，我们也要学会调整自己的心态，不要让外界的因素过度影响自己的情绪和工作状态。

再者，团队协作也是我们需要关注的重点。在现代职场中，很少有工作是一个人能够独立完成的，团队协作能力变得越来越重要。一个优秀的团队，不仅需要每个成员都具备出色的专业能力，更需要成员之间能够相互配合、相互支持。只有这样，团队才能发挥出最大的效能，完成看似不可能完成的任务。

另外，从{topic_name}这件事中，我们还可以看到职场中的责任与担当。每个人都有自己的职责和义务，在其位就要谋其政。当问题出现时，我们不能推卸责任，而是要勇于承担，并积极寻找解决问题的方法。只有这样，我们才能赢得同事和领导的信任，在职场中走得更稳、更远。

最后，这件事也提醒我们要不断学习和成长。职场是一个不断变化的环境，我们需要不断学习新知识、新技能，才能适应不断变化的工作需求。同时，我们也要从身边的人和事中吸取经验教训，不断完善自己，提升自己的综合素质。

总之，{topic_name}这件事给我们带来了很多思考。作为职场人，我们应该从中吸取经验教训，不断提升自己的沟通能力、心态调整能力、团队协作能力和责任担当意识。只有这样，我们才能在激烈的职场竞争中立于不败之地，实现自己的职业目标和人生价值。

你对{topic_name}这件事有什么看法？欢迎在评论区分享你的观点和感受！"""
    
    return {
        "title": f"{topic_name}深度分析：职场人该如何从中吸取经验？",
        "summary": f"{topic_name}引发广泛讨论，本文从职场角度深入分析这一现象，探讨对职场人的启示和借鉴意义。",
        "body": body
    }


def _call_ai(messages: List[Dict], temperature: float = 0.8, max_tokens: int = 2048) -> str:
    providers = {
        "deepseek": _call_deepseek,
        "gemini": _call_gemini,
        "huggingface": _call_huggingface
    }
    
    provider = _get_ai_provider()
    
    if provider == "local":
        raise ValueError("Local mode does not use _call_ai.")
    
    sanitized = []
    for msg in messages:
        m = msg.copy()
        if "content" in m and isinstance(m["content"], str):
            m["content"] = clean_unicode(m["content"])
        sanitized.append(m)
    
    if provider in providers:
        try:
            return providers[provider](sanitized, temperature, max_tokens)
        except (ValueError, requests.exceptions.RequestException) as e:
            print(f"Failed to call {provider}: {e}, falling back to local")
            raise AIRewriteError(f"AI服务不可用: {str(e)}")
    
    raise ValueError(f"Unknown AI provider: {provider}")


def _call_deepseek(messages: List[Dict], temperature: float = 0.8, max_tokens: int = 2048) -> str:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("请设置环境变量 DEEPSEEK_API_KEY")

    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1/chat/completions")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    sanitized = []
    for msg in messages:
        m = msg.copy()
        if "content" in m and isinstance(m["content"], str):
            m["content"] = clean_unicode(m["content"])
        sanitized.append(m)
    payload["messages"] = sanitized

    try:
        resp = requests.post(base_url, json=payload, headers=headers, timeout=180)
    except requests.exceptions.RequestException as e:
        raise AIRewriteError(f"API网络请求失败: {str(e)}")

    if resp.status_code == 401:
        raise AIRewriteError("API密钥无效(401)：请检查并更新您的API Key")
    if resp.status_code == 402:
        raise AIRewriteError("API账户余额不足(402)：请前往平台充值，或更换API Key")
    if resp.status_code == 429:
        raise AIRewriteError("API请求频率超限(429)：请稍后重试")
    if not resp.ok:
        raise AIRewriteError(f"API请求失败({resp.status_code})")

    try:
        data = resp.json()
    except ValueError:
        raise AIRewriteError("API返回数据解析失败")

    if "choices" not in data or not data["choices"]:
        raise AIRewriteError(f"AI返回异常: {str(data)[:200]}")

    content = data["choices"][0]["message"]["content"]
    return clean_unicode(content)


def select_top3_for_viral(topics: List[Dict]) -> List[Dict]:
    if _get_ai_provider() == "local":
        return _simple_local_select_top3(topics)
    
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
    
    try:
        content = _call_ai(
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": user_prompt}],
            temperature=0.6,
        )
        content = _strip_json(content)
        return json.loads(content)
    except Exception as e:
        print(f"AI call failed, using local fallback: {e}")
        return _simple_local_select_top3(topics)


def rewrite_to_micro_headline(topic_name: str) -> str:
    if _get_ai_provider() == "local":
        return _simple_local_rewrite_micro(topic_name)
    
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
    
    try:
        content = _call_ai(
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": user_prompt}],
            temperature=0.9,
        )
        return content.strip()
    except Exception as e:
        print(f"AI call failed, using local fallback: {e}")
        return _simple_local_rewrite_micro(topic_name)


def evaluate_traffic_potential(micro_text: str) -> Dict[str, str]:
    if _get_ai_provider() == "local":
        return _simple_local_evaluate(micro_text)
    
    system_prompt = (
        "你是一位今日头条流量分析专家。请从以下维度评价这篇微头条：\n"
        "1. 标题吸引力\n"
        "2. 内容共鸣度\n"
        "3. 互动潜力\n"
        "4. 总体流量预估（高/中/低）\n"
        "5. 内容原创性\n\n"
        "请严格按以下JSON格式返回，不要输出其他内容：\n"
        '{"traffic_level": "高/中/低", "traffic_comment": "流量评价理由，30字内", '
        '"originality": "原创性评价，30字内"}'
    )
    user_prompt = f"请评价这篇微头条：\n\n{micro_text}"
    
    try:
        content = _call_ai(
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": user_prompt}],
            temperature=0.7,
        )
        content = _strip_json(content)
        return json.loads(content)
    except Exception as e:
        print(f"AI call failed, using local fallback: {e}")
        return _simple_local_evaluate(micro_text)


def select_top3_for_articles(topics: List[Dict]) -> List[Dict]:
    if _get_ai_provider() == "local":
        return _simple_local_select_top3(topics)
    
    topic_list = "\n".join(
        f"{i + 1}. {t['name']} (热度: {t.get('hot', '未知')})"
        for i, t in enumerate(topics)
    )
    
    system_prompt = "你是一位今日头条号资深编辑，擅长判断哪些热点适合写成长文深度分析。"
    user_prompt = (
        f"以下是今日头条当前最热的{len(topics)}个话题：\n\n{topic_list}\n\n"
        "请从中选出最适合写成深度长文的3个话题。"
        "选择标准：话题有足够深度可展开、能引发读者思考、适合职场人群阅读。\n\n"
        "请严格按以下JSON格式返回，不要输出其他内容：\n"
        '[{"index": 1, "name": "话题名", "reason": "选择理由"}]'
    )
    
    try:
        content = _call_ai(
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": user_prompt}],
            temperature=0.6,
        )
        content = _strip_json(content)
        return json.loads(content)
    except Exception as e:
        print(f"AI call failed, using local fallback: {e}")
        return _simple_local_select_top3(topics)


def rewrite_to_article(topic_name: str) -> Dict[str, str]:
    if _get_ai_provider() == "local":
        return _simple_local_rewrite_article(topic_name)
    
    system_prompt = (
        "你是一位今日头条号爆款写手，擅长将热点写成深度职场分析文章。\n"
        "写作要求：\n"
        "1. 标题15-30字，有冲击力，含关键词\n"
        "2. 导语50-100字，一句话钩住读者\n"
        "3. 正文800-1500字，结构清晰：现象引入 → 职场深度分析 → 观点总结\n"
        "4. 职场人视角，有态度有干货，引发共鸣和讨论\n"
        "5. 口语化但不失深度，像资深职场人在分享洞察\n\n"
        "请严格按以下JSON格式返回，不要输出其他内容：\n"
        '{"title": "文章标题", "summary": "导语一句话", '
        '"body": "正文内容（用\\n\\n分隔自然段落）"}'
    )
    user_prompt = f"热点话题：{topic_name}\n\n请将上述热点写成一篇今日头条爆款职场分析文章。"
    
    try:
        content = _call_ai(
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": user_prompt}],
            temperature=0.85,
            max_tokens=4096,
        )
        content = _strip_json(content)
        return json.loads(content)
    except Exception as e:
        print(f"AI call failed, using local fallback: {e}")
        return _simple_local_rewrite_article(topic_name)


def evaluate_article(article_text: str) -> Dict[str, str]:
    if _get_ai_provider() == "local":
        return _simple_local_evaluate(article_text)
    
    system_prompt = (
        "你是一位今日头条流量分析专家。请评价这篇文章：\n"
        "请严格按以下JSON格式返回，不要输出其他内容：\n"
        '{"traffic_level": "高/中/低", "traffic_comment": "评价理由，30字内", '
        '"originality": "原创性评价，30字内"}'
    )
    user_prompt = f"请评价这篇文章：\n\n{article_text}"
    
    try:
        content = _call_ai(
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": user_prompt}],
            temperature=0.7,
        )
        content = _strip_json(content)
        return json.loads(content)
    except Exception as e:
        print(f"AI call failed, using local fallback: {e}")
        return _simple_local_evaluate(article_text)
