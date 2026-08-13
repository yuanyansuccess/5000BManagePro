# -*- coding: utf-8 -*-
"""
用户路由（API 层）
作者：袁燕
功能：用户增删查 + 登录认证（系统 RBAC）。不含 SQL（P18），无效参数 400（P10）。
"""
import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.schemas import UserCreate, UserOut, UserUpdate, ApiResp, LoginRequest, LoginResponse
from backend.services import data_service
from backend.db.models import User, USER_STATE

router = APIRouter(prefix="/api/users", tags=["users"])

# 简易 token 存储（生产环境应换成 JWT）
_login_tokens = {}


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    登录认证：账号+密码 → bcrypt 校验 → 返回 token + 用户信息。
    前端收到 token 后存 sessionStorage，后续请求带 Authorization: Bearer <token>。
    """
    if not payload.account or not payload.password:
        return LoginResponse(success=False, message="账号和密码不能为空")
    user, err_msg = data_service.DataService.authenticate(db, payload.account, payload.password)
    if not user:
        return LoginResponse(success=False, message=err_msg or "账号或密码错误")
    # 生成简易 token（生产改 JWT）
    token = hashlib.sha256(
        (user.account + secrets.token_hex(8)).encode("utf-8")
    ).hexdigest()
    _login_tokens[token] = user.user_id
    return LoginResponse(
        success=True,
        message="登录成功",
        token=token,
        user={
            "userId": user.user_id,
            "name": user.name,
            "account": user.account,
            "role": user.role,
            "authList": user.auth_list or "",
            "state": user.state,
        }
    )


@router.get("/me", response_model=ApiResp)
def get_me(authorization: str = Header(""), db: Session = Depends(get_db)):
    """根据 token 获取当前登录用户信息。"""
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    user_id = _login_tokens.get(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="未登录或 token 过期")
    from backend.dao.user_dao import UserDao
    user = UserDao.get_by_pk(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return ApiResp(data=UserOut.model_validate(user))


@router.get("", response_model=ApiResp)
def list_users(db: Session = Depends(get_db)):
    rows = data_service.DataService.list_users(db)
    return ApiResp(data=[UserOut.model_validate(r) for r in rows])


@router.post("", response_model=ApiResp)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if not payload.userId or not payload.name or not payload.account or not payload.role:
        raise HTTPException(status_code=400, detail="userId/name/account/role 必填")
    if payload.state not in USER_STATE:
        raise HTTPException(status_code=400, detail="state 取值非法")
    obj = User(
        user_id=payload.userId, name=payload.name, account=payload.account,
        password_hash="", role=payload.role,
        auth_list=payload.authList, state=payload.state,
    )
    if payload.password:
        obj.password_hash = data_service.DataService._hash_password(payload.password)
    data_service.DataService.create_user(db, obj)
    return ApiResp(data=UserOut.model_validate(obj))


@router.put("/{user_id}", response_model=ApiResp)
def update_user(user_id: str, payload: UserUpdate, db: Session = Depends(get_db)):
    """部分更新用户：仅更新 payload 中显式提供的字段。密码字段自动转 PBKDF2 哈希。"""
    # 显式映射 Schema 驼峰 → ORM 蛇形字段（避免 model_dump 别名问题）
    data = {}
    if payload.name is not None:
        data["name"] = payload.name
    if payload.account is not None:
        data["account"] = payload.account
    if payload.password is not None and payload.password:
        data["password_hash"] = data_service.DataService._hash_password(payload.password)
    if payload.role is not None:
        data["role"] = payload.role
    if payload.authList is not None:
        data["auth_list"] = payload.authList
    if payload.state is not None:
        data["state"] = payload.state
    obj = data_service.DataService.update_user(db, user_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="用户不存在")
    return ApiResp(data=UserOut.model_validate(obj))


@router.delete("/{user_id}", response_model=ApiResp)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    ok = data_service.DataService.delete_user(db, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="用户不存在")
    return ApiResp(message="已删除")
