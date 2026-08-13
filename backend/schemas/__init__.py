# -*- coding: utf-8 -*-
"""
API 数据契约（Pydantic）
作者：袁燕
功能：定义前后端 JSON 通讯的出入参模型。
      约定（继承智能柜 P13 铁律）：前端/JSON 统一驼峰；ORM/DB 内部用蛇形。
      实现：字段名用驼峰；alias_generator 自动把驼峰<->蛇形双向映射
            （验证接收驼峰、从 ORM 读蛇形属性、序列化输出驼峰）。
设计原则：高内聚（契约内聚）、低耦合（API 只认 schemas + Service，绝不 import DAO）。
"""
from pydantic import BaseModel, ConfigDict, AliasGenerator
from pydantic.alias_generators import to_snake, to_camel
from typing import Optional


class _Base(BaseModel):
    # from_attributes: 允许从 ORM 对象(蛇形属性)填充
    # populate_by_name: 允许用字段名(驼峰)或 alias 填充，灵活
    # alias_generator: 序列化输出驼峰(to_camel)，从 ORM/JSON 读蛇形(to_snake)
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=AliasGenerator(
            serialization_alias=to_camel,
            validation_alias=to_snake,
        ),
    )


# ===== 需求（RDM）=====
class RequirementCreate(_Base):
    reqId: str
    reqType: str
    reqName: str
    status: str = "草稿"
    source: Optional[str] = None
    baseline: Optional[str] = None


class RequirementOut(_Base):
    reqId: str
    reqType: str
    reqName: str
    status: str
    source: Optional[str] = None
    baseline: Optional[str] = None


# ===== 风险（PP/PMC）=====
class RiskCreate(_Base):
    riskId: str
    description: str
    level: Optional[str] = None
    owner: Optional[str] = None
    status: str = "打开"
    mitigation: Optional[str] = None


class RiskOut(_Base):
    riskId: str
    description: str
    level: Optional[str] = None
    owner: Optional[str] = None
    status: str
    mitigation: Optional[str] = None


# ===== 通用响应 =====
class ApiResp(BaseModel):
    status: str = "ok"
    message: Optional[str] = None
    data: Optional[object] = None


# ===== 风险（PP/PMC）— 输出 =====
class RiskOut(_Base):
    riskId: str
    description: str
    level: Optional[str] = None
    owner: Optional[str] = None
    status: str
    mitigation: Optional[str] = None


# ===== 相关方（PP A14）=====
class StakeholderCreate(_Base):
    role: str
    name: str
    responsibility: Optional[str] = None
    joinPhase: Optional[str] = None


class StakeholderOut(_Base):
    role: str
    name: str
    responsibility: Optional[str] = None
    joinPhase: Optional[str] = None


# ===== 告警日志 =====
class AlertCreate(_Base):
    level: str = "warn"
    category: Optional[str] = None
    title: str
    detail: Optional[str] = None
    source: Optional[str] = None
    status: str = "未处理"


class AlertOut(_Base):
    id: int
    level: str
    category: Optional[str] = None
    title: str
    detail: Optional[str] = None
    source: Optional[str] = None
    status: str
    createdAt: Optional[object] = None


# ===== 用户（RBAC）=====
class UserCreate(_Base):
    userId: str
    name: str
    account: str
    password: Optional[str] = None  # 明文密码，仅 API 接收，Service 层转 bcrypt hash 落盘
    role: str
    authList: Optional[str] = None
    state: str = "active"


class UserOut(_Base):
    userId: str
    name: str
    account: str
    role: str
    authList: Optional[str] = None
    state: str


class UserUpdate(_Base):
    """用户部分更新（所有字段可选，只更新传了值的字段）。"""
    name: Optional[str] = None
    account: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    authList: Optional[str] = None
    state: Optional[str] = None


# ===== 登录 =====
class LoginRequest(BaseModel):
    account: str
    password: str


class LoginResponse(BaseModel):
    success: bool = False
    message: str = ""
    token: Optional[str] = None
    user: Optional[dict] = None


# ===== SVN 集成（提交钩子 + 客户端服务）=====
class SvnCommitIn(BaseModel):
    """钩子推送的提交记录（平台入库）。"""
    repoName: str
    commitUser: str
    revision: int
    commitTime: Optional[str] = None
    changedFiles: Optional[str] = None
    projectName: Optional[str] = None
    rawLog: Optional[str] = None
    secret: Optional[str] = None


class SvnCommitOut(_Base):
    id: int
    repoName: str
    commitUser: str
    revision: int
    commitTime: Optional[str] = None
    changedFiles: Optional[str] = None
    projectName: Optional[str] = None


class ClientWatchIn(BaseModel):
    """用户在平台配置关注路径。"""
    machineId: str
    userName: Optional[str] = None
    watchPath: str


class ClientWatchOut(_Base):
    id: int
    machineId: str
    userName: Optional[str] = None
    watchPath: str
    lastUpdateRev: int = 0
    lastUpdateStatus: str = "pending"
    lastUpdateMsg: Optional[str] = None


class ClientUpdateQuery(BaseModel):
    """客户端轮询待更新指令。"""
    machineId: str


class ClientUpdateItem(_Base):
    watchId: int
    watchPath: str
    targetRev: int


class ClientReportIn(BaseModel):
    """客户端回报更新结果。"""
    machineId: str
    watchId: int
    status: str
    msg: Optional[str] = None
    targetRev: Optional[int] = None
