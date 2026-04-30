from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from backend.config import get_settings
from backend.api.routes import chat, phones
from pathlib import Path
import asyncio
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(title="手机选购助手API", version="0.1.0")

# 静态文件服务 - 必须在 include_router 之前 mount
IMAGES_DIR = Path(__file__).parent.parent / "images"
if IMAGES_DIR.exists():
    app.mount("/images", StaticFiles(directory=str(IMAGES_DIR.absolute())), name="images")

# 中间件
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175",
                   "http://localhost:5176", "http://localhost:5177", "http://localhost:5178",
                   "http://localhost:5179", "http://localhost:5180"],
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
    return {"status": "healthy"}


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


@app.on_event("startup")
async def startup_event():
    """应用启动时启动后台任务"""
    asyncio.create_task(cleanup_sessions_periodically())
