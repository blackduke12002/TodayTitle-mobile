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

    result = "".join(cleaned)
    # Remove control characters except tab, newline, carriage return
    result = re.sub("".join([
        "[",
        chr(0), "-", chr(8),  # 0x00-0x08
        chr(11), "-", chr(12),  # 0x0B-0x0C
        chr(14), "-", chr(31),  # 0x0E-0x1F
        chr(127), "-", chr(159),  # 0x7F-0x9F
        "]"
    ]), "", result)
    result = result.replace(chr(0x200B), "").replace(chr(0x200C), "").replace(chr(0x200D), "")
    result = result.replace(chr(0xFEFF), "").replace(chr(0xA0), " ")
    return result.strip()
