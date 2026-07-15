"""
第十阶段：敏感信息脱敏 (Redactor)

用正则表达式识别常见手机号和模拟 API Key，
替换为固定占位符，避免敏感信息进入日志和评估报告。
"""

import re

# 中国大陆手机号：1[3-9] + 9 位数字
PHONE_RE = re.compile(r"1[3-9]\d{9}")

# 模拟 API Key 格式：sk- 开头 + 字母/数字/下划线/连字符
API_KEY_RE = re.compile(r"sk-[A-Za-z0-9_-]+")


def redact_sensitive(text: str) -> str:
    """将手机号和 API Key 替换为 [PHONE] / [API_KEY] 占位符。"""
    text = PHONE_RE.sub("[PHONE]", text)
    text = API_KEY_RE.sub("[API_KEY]", text)
    return text


if __name__ == "__main__":
    test_input = "用户手机号 13812345678，密钥 sk-test-123456，另一个号 13900001111"
    result = redact_sensitive(test_input)
    expected = "用户手机号 [PHONE]，密钥 [API_KEY]，另一个号 [PHONE]"
    print(f"输入:   {test_input}")
    print(f"输出:   {result}")
    print(f"期望:   {expected}")
    print(f"通过:   {result == expected}")
