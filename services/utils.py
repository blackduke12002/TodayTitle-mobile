"""Shared utility functions for TodayTitle project."""
import re


def clean_unicode(text: str) -> str:
    """清理字符串中的非法Unicode字符。"""
    if not text:
        return ""
    
    cleaned = []
    i = 0
    while i < len(text):
        code = ord(text[i])
        if 0xD800 <= code <= 0xDBFF:
            if i + 1 < len(text):
                next_code = ord(text[i + 1])
                if 0xDC00 <= next_code <= 0xDFFF:
                    cleaned.append(text[i])
                    cleaned.append(text[i + 1])
                    i += 2
                    continue
            i += 1
            continue
        elif 0xDC00 <= code <= 0xDFFF:
            i += 1
            continue
        else:
            cleaned.append(text[i])
            i += 1
    
    result = ''.join(cleaned)
    result = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', result)
    return result.strip()
