# -*- coding: utf-8 -*-
"""
ORM 模型（数据层表结构定义，与存储格式解耦）
作者：袁燕
功能：定义全部领域表。标识符（OR/SR/BF/PS/GS）作为主外键，对应方案 4.2/5.4。
      状态枚举集中此处，前端不发明状态词（继承智能柜 P14 铁律）。
设计原则：高内聚（表结构内聚）、低耦合（上层通过 DAO 访问，不直接 import 模型写 SQL）。
"""
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, Boolean, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# ===== 状态枚举（集中定义，全局唯一真相，前端对齐用）=====
REQ_STATUS = ["草稿", "评审中", "已基线", "实施中", "已关闭"]
RISK_STATUS = ["打开", "处理中", "已关闭"]
CI_STATUS = ["草稿", "受控", "变更中", "已发布"]
USER_STATE = ["active", "disabled"]

# ===== SVN 集成（提交钩子 + 客户端服务）=====
# 客户端更新状态枚举（集中定义，前端对齐用）
CLIENT_UPDATE_STATUS = ["pending", "updating", "success", "failed"]


class Requirement(Base):
    """需求（RDM）：需求跟踪矩阵/状态表，req_id 为唯一键(OR/SR/DR/CT)"""
    __tablename__ = "requirements"
    req_id = Column(String(64), primary_key=True)
    req_type = Column(String(32), nullable=False)
    req_name = Column(String(255), nullable=False)
    status = Column(String(16), default="草稿")
    source = Column(String(255))
    baseline = Column(String(64))


class SchedulePhase(Base):
    """进度阶段（PP/PMC）：5 阶段进度与工作量，phase_no 主键"""
    __tablename__ = "schedule_phases"
    phase_no = Column(Integer, primary_key=True)
    phase_name = Column(String(32), nullable=False)
    ratio = Column(String(16))
    eng_md = Column(Float)
    mgr_md = Column(Float)
    start_date = Column(String(16))
    end_date = Column(String(16))
    milestone = Column(String(255))


class Workload(Base):
    """工作量（MA 测量源）"""
    __tablename__ = "workloads"
    wid = Column(Integer, primary_key=True, autoincrement=True)
    phase = Column(String(32))
    role = Column(String(32))
    man_day = Column(Float)
    note = Column(String(255))


class Defect(Base):
    """缺陷（MA 测量源）"""
    __tablename__ = "defects"
    did = Column(Integer, primary_key=True, autoincrement=True)
    phase = Column(String(32))
    severity = Column(String(16))
    count = Column(Integer)
    source = Column(String(64))


class Nonconformity(Base):
    """不符合项（PQA）：A27/A28/A29"""
    __tablename__ = "nonconformities"
    ncid = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    level = Column(String(16))
    owner = Column(String(64))
    status = Column(String(16), default="打开")
    measure = Column(Text)


class ConfigItem(Base):
    """配置项（CM）：A51~A59，ci_id 唯一键"""
    __tablename__ = "config_items"
    ci_id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    baseline = Column(String(64))
    status = Column(String(16), default="草稿")
    path = Column(String(255))


class Risk(Base):
    """风险（PP/PMC）：A11，risk_id 唯一键"""
    __tablename__ = "risks"
    risk_id = Column(String(64), primary_key=True)
    description = Column(String(255), nullable=False)
    level = Column(String(16))
    owner = Column(String(64))
    status = Column(String(16), default="打开")
    mitigation = Column(Text)


class Stakeholder(Base):
    """相关方（PP）：A14"""
    __tablename__ = "stakeholders"
    role = Column(String(64), primary_key=True)
    name = Column(String(64), nullable=False)
    responsibility = Column(Text)
    join_phase = Column(String(32))


class TemplateAnchor(Base):
    """模板锚点取值（锚点引擎数据源，兼容 devplan 等模板）"""
    __tablename__ = "template_anchors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    template_name = Column(String(64), nullable=False)
    anchor_key = Column(String(64), nullable=False)
    anchor_value = Column(Text)
    __table_args__ = (UniqueConstraint("template_name", "anchor_key", name="uk_tpl_anchor"),)


class User(Base):
    """用户与权限（系统，RBAC）。password_hash 存储 bcrypt hash，原始密码绝不落盘。"""
    __tablename__ = "users"
    user_id = Column(String(64), primary_key=True)
    name = Column(String(64), nullable=False)
    account = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False, default="")
    role = Column(String(16), nullable=False)
    auth_list = Column(String(255))
    state = Column(String(16), default="active")


class AuditLog(Base):
    """操作审计（方案 5.3 RBAC 留痕）"""
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(String(64))
    action = Column(String(64))
    target = Column(String(128))
    detail = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class AlertLog(Base):
    """告警日志（基础数据预警）：校核异常/数据不一致/超时"""
    __tablename__ = "alert_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(16), default="warn")          # warn / error / info
    category = Column(String(32))                         # 校核异常 / 数据不一致 / 超时
    title = Column(String(255), nullable=False)
    detail = Column(Text)
    source = Column(String(64))                           # 触发模块（PP/PMC/RDM...）
    status = Column(String(16), default="未处理")         # 未处理 / 已处理 / 忽略
    created_at = Column(DateTime, default=datetime.now)


ALERT_STATUS = ["未处理", "已处理", "忽略"]
ALERT_LEVEL = ["info", "warn", "error"]


class SvnCommitLog(Base):
    """SVN 提交日志（钩子推送入库）。一条提交记录一次。"""
    __tablename__ = "svn_commit_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_name = Column(String(64), nullable=False)        # 仓库名 R105/R120/R121
    commit_user = Column(String(64), nullable=False)      # 提交者账号
    revision = Column(Integer, nullable=False)           # 版本号
    commit_time = Column(String(32))                      # 提交时间(字符串，svnlook 原始格式)
    changed_files = Column(Text)                          # 改动文件清单(每行一条路径)
    project_name = Column(String(128))                    # 项目名称(钩子传入)
    raw_log = Column(Text)                                # 原始提交日志
    created_at = Column(DateTime, default=datetime.now)


class ClientWatch(Base):
    """客户端关注路径（用户在平台自己配置）。客户端服务据此接收更新指令。"""
    __tablename__ = "client_watch"
    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String(128), nullable=False)      # 客户端机器标识(电脑名+用户)
    user_name = Column(String(64))                        # 关联平台用户账号
    watch_path = Column(String(512), nullable=False)      # 关注的 SVN 路径(如 R105/trunk/需求开发与管理)
    last_update_rev = Column(Integer, default=0)          # 最近一次更新到的版本
    last_update_status = Column(String(16), default="pending")  # pending/updating/success/failed
    last_update_msg = Column(String(512))                 # 最近更新结果描述
    updated_at = Column(DateTime, default=datetime.now)
