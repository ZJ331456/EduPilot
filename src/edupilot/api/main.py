"""FastAPI 入口：Vue 开发服务器通过 Vite 代理访问 /api/v1。"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from edupilot.api.routers import chat, evaluation, graph, health, plan, profile
from edupilot.config.settings import ensure_data_subdirs, get_settings


def create_app() -> FastAPI:
    ensure_data_subdirs()
    settings = get_settings()
    app = FastAPI(title="EduPilot API", version="0.1.0")

    origins = [o.strip() for o in settings.api_cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(graph.router, prefix="/api/v1")
    app.include_router(profile.router, prefix="/api/v1")
    app.include_router(plan.router, prefix="/api/v1")
    app.include_router(evaluation.router, prefix="/api/v1")
    return app


app = create_app()
