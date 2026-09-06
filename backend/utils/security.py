"""
安全工具模块 - 防止Prompt注入攻击
"""
import re
from typing import Optional


# 危险模式列表 - 检测潜在的Prompt注入攻击
DANGEROUS_PATTERNS = [
    # 角色扮演/身份欺骗
    r"ignore\s+(previous|all|above)\s+(instructions?|prompts?|rules?)",
    r"you\s+are\s+(now|a)\s+",
    r"act\s+as\s+(if\s+you\s+are\s+)?a?\s*",
    r"pretend\s+(to\s+be|you\s+are)\s+",
    r"role[\s-]?play\s+as\s+",

    # 系统指令绕过
    r"system\s*:\s*",
    r"<\s*system\s*>",
    r"\[?\s*system\s*\]?\s*:",
    r"override\s+(your\s+)?(instructions?|prompts?|rules?)",

    # 输出操纵
    r"output\s+(only\s+)?(the\s+)?following",
    r"print\s+(exactly\s+)?",
    r"respond\s+(only\s+)?with\s+",
    r"say\s+(exactly\s+)?",

    # 数据泄露尝试
    r"reveal\s+(your\s+)?(prompt|instructions?|system)",
    r"show\s+(me\s+)?(your\s+)?(prompt|instructions?)",
    r"what\s+(is|are)\s+(your\s+)?(instructions?|prompts?)",
    r"repeat\s+(your\s+)?(instructions?|prompts?)",

    # 特殊Token注入
    r"<\s*\|\s*.*?\s*\|\s*>",  # <|...|>
    r"\[\s*INST\s*\]",  # [INST]
    r"<\s*\|\s*im_(start|end)\s*\|\s*>",  # ChatML tokens
]

# 编译正则表达式
COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERNS]

# 最大输入长度
MAX_INPUT_LENGTH = 2000


def sanitize_input(user_input: str) -> str:
    """
    清理用户输入（长度限制 + 控制字符过滤）

    注意：这里不做 HTML 转义。转义会破坏 LLM 上下文和"引用用户原话"功能
    （用户会看到 &quot; 等实体）；XSS 由前端 React 的自动转义负责。
    防止Prompt注入靠 detect_injection_attempt + 长度/控制字符限制。

    Args:
        user_input: 用户原始输入

    Returns:
        清理后的安全输入
    """
    if not user_input:
        return ""

    # 限制长度
    if len(user_input) > MAX_INPUT_LENGTH:
        user_input = user_input[:MAX_INPUT_LENGTH]

    # 移除控制字符（保留换行和制表符）
    user_input = ''.join(
        char for char in user_input
        if char.isprintable() or char in '\n\t'
    )

    return user_input.strip()


def detect_injection_attempt(user_input: str) -> tuple[bool, Optional[str]]:
    """
    检测潜在的Prompt注入攻击

    Args:
        user_input: 用户输入

    Returns:
        (是否检测到攻击, 模式类别描述)

        描述只返回固定的类别文案，不回显命中内容——
        回显具体匹配片段会让攻击者据此探测规则库 (REVIEW_REPORT H8)
    """
    if not user_input:
        return False, None

    for pattern in COMPILED_PATTERNS:
        match = pattern.search(user_input)
        if match:
            return True, "可疑模式"

    return False, None


def validate_chat_input(message: str) -> tuple[bool, str, Optional[str]]:
    """
    验证聊天输入

    Args:
        message: 用户消息

    Returns:
        (是否有效, 处理后的消息, 错误信息)
    """
    if not message or not message.strip():
        return False, "", "消息不能为空"

    # 检测注入攻击
    is_attack, attack_pattern = detect_injection_attempt(message)
    if is_attack:
        return False, "", f"输入包含不允许的内容: {attack_pattern}"

    # 清理输入
    sanitized = sanitize_input(message)

    if not sanitized:
        return False, "", "消息内容无效"

    return True, sanitized, None
