import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from backend.config import settings
from backend.database import init_db
from backend.routers import proxy, config, usage, alerts
from backend.services.monitor import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="APITokenWatcher", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(proxy.router)
app.include_router(config.router)
app.include_router(usage.router)
app.include_router(alerts.router)

# 托管前端静态文件（如果存在）
# 打包后静态文件在 _MEIPASS 目录中，开发时在 backend/static/
if getattr(sys, "frozen", False):
    static_dir = Path(sys._MEIPASS) / "backend" / "static"
else:
    static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
