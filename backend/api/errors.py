"""
统一错误响应模型

定义标准化的错误响应格式，确保 API 返回一致的错误结构。
"""

from enum import Enum
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """错误码枚举

    遵循语义化命名规则：
    - 前缀表示错误类别
    - 后缀表示具体错误类型
    """

    # 验证类错误 (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"  # 通用验证失败
    INVALID_INPUT = "INVALID_INPUT"  # 输入格式错误
    INVALID_PRICE_RANGE = "INVALID_PRICE_RANGE"  # 价格区间无效
    MESSAGE_TOO_LONG = "MESSAGE_TOO_LONG"  # 消息超出长度限制
    INVALID_SESSION = "INVALID_SESSION"  # 会话无效或过期

    # 资源类错误 (404)
    NOT_FOUND = "NOT_FOUND"  # 通用资源不存在
    PHONE_NOT_FOUND = "PHONE_NOT_FOUND"  # 手机不存在
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"  # 会话不存在

    # LLM 服务类错误 (5xx)
    LLM_ERROR = "LLM_ERROR"  # LLM 调用失败
    LLM_TIMEOUT = "LLM_TIMEOUT"  # LLM 调用超时
    LLM_RATE_LIMITED = "LLM_RATE_LIMITED"  # LLM 限流

    # 安全类错误 (403)
    FORBIDDEN = "FORBIDDEN"  # 禁止访问
    SECURITY_VIOLATION = "SECURITY_VIOLATION"  # 安全违规（如注入攻击）
    RATE_LIMITED = "RATE_LIMITED"  # 请求频率超限

    # 服务端错误 (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"  # 内部服务错误
    DATABASE_ERROR = "DATABASE_ERROR"  # 数据库错误
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"  # 服务不可用


class ErrorResponse(BaseModel):
    """统一错误响应模型

    所有 API 错误应返回此格式的响应，确保前端能够统一处理。
    """

    code: ErrorCode = Field(
        ...,
        description="错误码，用于程序判断错误类型"
    )
    message: str = Field(
        ...,
        description="人类可读的错误信息，可直接展示给用户"
    )
    detail: Optional[dict[str, Any]] = Field(
        default=None,
        description="错误详情，包含调试信息或具体错误字段"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="错误发生时间，ISO 8601 格式"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": "PHONE_NOT_FOUND",
                "message": "手机不存在",
                "detail": {"phone_id": 999},
                "timestamp": "2026-05-02T10:30:00.000000"
            }
        }


def error_response(
    code: ErrorCode,
    message: str,
    detail: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """快速构造错误响应字典

    Args:
        code: 错误码
        message: 错误信息
        detail: 可选的错误详情

    Returns:
        可直接返回的字典格式错误响应
    """
    return ErrorResponse(
        code=code,
        message=message,
        detail=detail
    ).model_dump()


def sse_error_response(
    code: ErrorCode,
    message: str,
    detail: Optional[dict[str, Any]] = None
) -> str:
    """构造 SSE 格式的错误响应

    用于流式接口返回错误信息。

    Args:
        code: 错误码
        message: 错误信息
        detail: 可选的错误详情

    Returns:
        SSE 格式的字符串，可直接 yield
    """
    import json
    error_data = error_response(code, message, detail)
    return f"data: {json.dumps({'type': 'error', 'data': error_data}, ensure_ascii=False)}\n\n"
