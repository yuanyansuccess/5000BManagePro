# -*- coding: utf-8 -*-
"""
FastAPI 主入口
作者：袁燕
功能：平台后端服务入口。挂载各过程域路由，启动时自动建表。
      前后端通过 /api/* JSON 通讯，前端绝不直连数据库。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.session import init_db
from backend.api import requirements, risks, stakeholders, alerts, users, svn

app = FastAPI(title="GJB5000B 管理平台后端", version="0.1.0")

# 跨域：前端独立启动（如 5500/直接文件）需允许跨域访问 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(requirements.router)
app.include_router(risks.router)
app.include_router(stakeholders.router)
app.include_router(alerts.router)
app.include_router(users.router)
app.include_router(svn.router)


@app.on_event("startup")
def on_startup():
    init_db()  # 启动建表/补列（继承智能柜 P22）


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "gjb5000b-backend"}
