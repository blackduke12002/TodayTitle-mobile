"""Fetch Toutiao hot topics — TenAPI primary, direct scrape fallback."""
import requests
import re
import json
from typing import List, Dict

try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False

from .utils import clean_unicode

TENAPI_URL = "https://tenapi.cn/v2/toutiaohot"
TOUTIAO_URL = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"


class HotspotFetchError(Exception):
    pass


def fetch_hot_topics(limit: int = 5) -> List[Dict[str, str]]:
    """Returns [{name, url, hot}, ...], up to `limit` items."""
    try:
        return _fetch_from_tenapi(limit)
    except Exception as e1:
        try:
            return _fetch_from_toutiao(limit)
        except Exception as e2:
            raise HotspotFetchError(
                f"所有获取方式均失败。API: {e1}, 直接抓取: {e2}"
            )


def _fetch_from_tenapi(limit: int) -> List[Dict]:
    resp = requests.get(TENAPI_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 200:
        raise HotspotFetchError(f"API返回错误: {data.get('msg', '未知')}")

    items = data.get("data", [])
    if not items:
        raise HotspotFetchError("API返回空数据")

    result = []
    for item in items[:limit]:
        result.append({
            "name": clean_unicode(item.get("name", "")),
            "url": clean_unicode(item.get("url", "")),
            "hot": _format_hot(item.get("hot", "")),
        })
    return result


def _fetch_from_toutiao(limit: int) -> List[Dict]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.toutiao.com/",
    }
    
    resp = requests.get(TOUTIAO_URL, headers=headers, timeout=15)
    resp.raise_for_status()
    
    content_encoding = resp.headers.get("Content-Encoding", "")
    
    try:
        if content_encoding == "br" and len(resp.content) > 0 and BROTLI_AVAILABLE:
            try:
                decompressed = brotli.decompress(resp.content)
                data = json.loads(decompressed.decode("utf-8"))
            except Exception:
                resp.encoding = "utf-8"
                data = json.loads(resp.text)
        else:
            resp.encoding = "utf-8"
            data = json.loads(resp.text)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        if content_encoding == "br" and BROTLI_AVAILABLE:
            try:
                decompressed = brotli.decompress(resp.content)
                data = json.loads(decompressed.decode("utf-8"))
            except Exception as e2:
                raise HotspotFetchError(f"解析失败: {e2}")
        else:
            raise HotspotFetchError(f"解析失败: {e}")

    items = data.get("data", [])
    if not items:
        raise HotspotFetchError("头条页面返回空数据")

    result = []
    for item in items[:limit]:
        result.append({
            "name": clean_unicode(item.get("Title", "")),
            "url": clean_unicode(item.get("Url", "")),
            "hot": _format_hot(item.get("HotValue", "")),
        })
    return result


def _format_hot(value) -> str:
    """Format raw hot value to readable string like '502.3万'."""
    if isinstance(value, str) and value:
        return value
    if isinstance(value, (int, float)):
        v = float(value)
        if v >= 1_0000_0000:
            return f"{v / 1_0000_0000:.1f}亿"
        if v >= 1_0000:
            return f"{v / 1_0000:.1f}万"
        return str(int(v))
    return str(value) if value else ""
