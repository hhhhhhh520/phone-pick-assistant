from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from backend.config import get_settings
from backend.api.routes import chat, phones
from backend.api.errors import ErrorCode, ErrorResponse
from backend.services.llm import LLMError
from pathlib import Path
from contextlib import asynccontextmanager
import asyncio
import logging
import sys

settings = get_settings()

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)
logger.info(f"Starting application in {settings.app_env} mode")


# 后台任务：定期清理过期会话
async def cleanup_sessions_periodically():
    """每5分钟清理一次过期会话"""
    from backend.services.session import SessionService
    session_service = SessionService()
    while True:
        await asyncio.sleep(300)  # 5分钟
        try:
            count = session_service.cleanup_expired_sessions()
            if count > 0:
                logger.info(f"Cleaned up {count} expired sessions")
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    asyncio.create_task(cleanup_sessions_periodically())
    yield
    # 关闭时（如需要可添加清理逻辑）


app = FastAPI(title="手机选购助手API", version="0.1.0", lifespan=lifespan)

# 静态文件服务 - 必须在 include_router 之前 mount
IMAGES_DIR = Path(__file__).parent.parent / "images"
if IMAGES_DIR.exists():
    app.mount("/images", StaticFiles(directory=str(IMAGES_DIR.absolute())), name="images")

# 中间件
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS配置 - 开发环境和生产环境都使用白名单模式
# 白名单通过环境变量 cors_origins 配置，默认允许本地开发端口
# 注意：allow_origins=["*"] 与 allow_credentials=True 组合在浏览器中会报错
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),  # 统一使用白名单
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由 - 必须在 mount 之后
app.include_router(chat.router)
app.include_router(phones.router)


@app.get("/")
async def root():
    return {"message": "手机选购助手API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """
    健康检查端点，包含数据库连接状态和LLM服务可达性检查

    返回格式：
    - status: "healthy" | "degraded" | "unhealthy"
    - latency_ms: 总检查耗时（毫秒）
    - components: {
        database: {status, latency_ms, error?},
        llm: {status, model, error?}
      }

    降级场景：
    - healthy: 所有组件正常
    - degraded: 部分组件异常（如LLM不可用但数据库正常）
    - unhealthy: 关键组件异常（数据库不可用）
    """
    from backend.models.domain import SessionLocal
    from backend.services.llm import LLMService
    from sqlalchemy import text
    import time

    start_time = time.time()
    components = {}

    # 数据库检查
    db_status = {"status": "connected", "latency_ms": None}
    try:
        db_start = time.time()
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        db_status["latency_ms"] = round((time.time() - db_start) * 1000, 2)
    except Exception as e:
        db_status["status"] = "error"
        db_status["error"] = str(e)[:100]
    components["database"] = db_status

    # LLM服务检查
    llm_service = LLMService()
    llm_status = await llm_service.health_check()
    components["llm"] = llm_status

    # 计算整体状态
    total_latency = round((time.time() - start_time) * 1000, 2)

    db_healthy = db_status["status"] == "connected"
    llm_healthy = llm_status["status"] == "available"

    if db_healthy and llm_healthy:
        overall_status = "healthy"
    elif db_healthy:
        # 数据库正常但LLM异常：降级运行
        overall_status = "degraded"
    else:
        # 数据库异常：整体不健康
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "latency_ms": total_latency,
        "components": components
    }


@app.get("/stats/sessions")
async def session_stats():
    """获取会话统计信息"""
    from backend.services.session import sessions, _sessions_lock

    with _sessions_lock:
        total_sessions = len(sessions)
        total_messages = sum(len(data.session.messages) for data in sessions.values())

    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "avg_messages_per_session": round(total_messages / total_sessions, 2) if total_sessions > 0 else 0,
    }



@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """处理 HTTP 异常

    将 FastAPI/Starlette 的 HTTP 异常转换为统一的 ErrorResponse 格式。
    """
    # 根据状态码映射到对应的错误码
    code_map = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.FORBIDDEN,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMITED,
        500: ErrorCode.INTERNAL_ERROR,
        502: ErrorCode.SERVICE_UNAVAILABLE,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }

    code = code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)

    # 特殊处理 404
    if exc.status_code == 404:
        message = f"请求的资源不存在: {request.url.path}"
    else:
        message = exc.detail or "请求处理失败"

    error = ErrorResponse(code=code, message=message, detail={"status_code": exc.status_code})
    return JSONResponse(
        status_code=exc.status_code,
        content=error.model_dump()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理 Pydantic 验证错误

    将请求体验证错误转换为友好的错误信息。
    """
    # 提取验证错误详情
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })

    error = ErrorResponse(
        code=ErrorCode.VALIDATION_ERROR,
        message="请求参数验证失败",
        detail={"errors": errors}
    )
    return JSONResponse(
        status_code=422,
        content=error.model_dump()
    )


@app.exception_handler(LLMError)
async def llm_exception_handler(request: Request, exc: LLMError) -> JSONResponse:
    """处理 LLM 服务错误

    将 LLM 相关错误转换为标准响应格式，避免暴露内部实现细节。
    """
    error_message = str(exc)

    # 根据错误信息判断错误类型
    if "timeout" in error_message.lower():
        code = ErrorCode.LLM_TIMEOUT
        message = "AI 服务响应超时，请稍后重试"
    elif "rate" in error_message.lower() or "limit" in error_message.lower():
        code = ErrorCode.LLM_RATE_LIMITED
        message = "AI 服务繁忙，请稍后重试"
    else:
        code = ErrorCode.LLM_ERROR
        message = "AI 服务暂时不可用，请稍后重试"

    logger.error(f"LLM error on {request.url.path}: {error_message}")

    error = ErrorResponse(
        code=code,
        message=message,
        detail={"original_error": error_message[:200]}  # 限制长度
    )
    return JSONResponse(
        status_code=503,
        content=error.model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理未捕获的通用异常

    作为最后的防线，确保任何异常都返回统一格式。
    生产环境不暴露具体错误信息。
    """
    # 记录完整错误日志
    logger.exception(f"Unhandled exception on {request.url.path}: {type(exc).__name__}: {exc}")

    # 生产环境不暴露错误详情
    if settings.app_env == "production":
        detail = None
    else:
        detail = {
            "type": type(exc).__name__,
            "message": str(exc)[:200]
        }

    error = ErrorResponse(
        code=ErrorCode.INTERNAL_ERROR,
        message="服务器内部错误，请稍后重试",
        detail=detail
    )
    return JSONResponse(
        status_code=500,
        content=error.model_dump()
    )
