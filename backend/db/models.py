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
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# ===== 状态枚举（集中定义，全局唯一真相，前端对齐用）=====
REQ_STATUS = ["草稿", "评审中", "已基线", "实施中", "已关闭"]
RISK_STATUS = ["未发生", "已发生", "已关闭"]
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


class ProjectMember(Base):
    """项目人员（PP 项目组织与人员，文档签署/角色分配的基础）。按项目维度隔离。
    -> 用户管理「项目人员」模块（可编辑），并作为文档生成角色来源。"""
    __tablename__ = "project_members"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(32), nullable=False, default="R105")
    name = Column(String(32), nullable=False)          # 姓名
    role = Column(String(64))                          # 角色，如 软件负责人
    team = Column(String(32))                          # 所属组，如 软件/测试/配置
    no = Column(String(32))                            # 人员编号
    svn = Column(String(255))                          # SVN 个人路径
    auth = Column(String(128))                         # 权限/职责范围
    seq = Column(Integer, default=0)                   # 排序


class EstItem(Base):
    """软件估算收敛项（PP 估算，对标 R105 代码个人估算汇总表 R105-PP-GH-01/02）。
    结构：轮次 + 软件配置项 + 部件(功能点) + 三位估算人（辛峥峰/罗臻/马慧芳）
         + 偏差(Max-Min) + 平均值 + 相对偏差(Dev/Avg) + 收敛状态。
    收敛规则：相对偏差 <= 20% 判定"已收敛"，否则"需再估"（继续下一轮）。
    按项目维度隔离。"""
    __tablename__ = "est_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(32), nullable=False, default="R105")
    round_no = Column(Integer, default=1)              # 估算轮次：1=第1轮，2=第2轮，3=第3轮
    cfg_item = Column(String(128))                     # 软件配置项，如 触摸屏控制软件
    wbs2 = Column(String(128))                         # 部件（配置项下的功能点/模块）
    est1 = Column(String(32))                          # 估算人1：辛峥峰
    est2 = Column(String(32))                          # 估算人2：罗臻
    est3 = Column(String(32))                          # 估算人3：马慧芳
    deviation = Column(String(32))                     # 偏差 = Max-Min
    avg_val = Column(String(32))                       # 平均值
    rel_dev = Column(String(32))                       # 相对偏差 = Dev/Avg
    converge = Column(String(32))                      # 收敛状态：已收敛 / 需再估
    is_total = Column(Integer, default=0)              # 1=合计行
    seq = Column(Integer, default=0)                   # 排序


class SchedulePhase(Base):
    """进度阶段（PP/PMC）：5 阶段进度与工作量。按项目维度隔离。
    -> {{table.schedule}} 进度计划表 / {{table.stakeholder_plan}} 参与矩阵。"""
    __tablename__ = "schedule_phases"
    id = Column(Integer, primary_key=True, autoincrement=True)  # 自增主键
    project_id = Column(String(32), nullable=False, default="R105")  # 项目维度（项目方铁律）
    phase_no = Column(Integer, nullable=False)                   # 阶段序号 1..5
    phase_name = Column(String(32), nullable=False)
    ratio = Column(String(16))
    eng_md = Column(Float)
    mgr_md = Column(Float)
    start_date = Column(String(16))
    end_date = Column(String(16))
    milestone = Column(String(255))


class ScheduleTask(Base):
    """进度任务项（维度2：全部任务，来源 R105软件进度表 .mpp）。
    为双周任务表生成做储备：阶段归属 + 任务名 + 层级 + 摘要标记 +
    计划开始/完成 + 工期(天) + 负责人 + 完成百分比 + 前置任务。按项目维度隔离。"""
    __tablename__ = "schedule_tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(32), nullable=False, default="R105")
    phase_name = Column(String(64))          # 所属阶段（关联 schedule_phases.phase_name）
    task_no = Column(Integer, default=0)     # 任务序号（展示顺序）
    outline_level = Column(Integer, default=1)  # 层级：1=阶段(摘要)，2=具体任务
    is_summary = Column(Integer, default=0)  # 1=摘要任务（阶段/汇总行）
    task_name = Column(String(255), nullable=False)
    plan_start = Column(String(16))          # 计划开始 yyyy-mm-dd
    plan_finish = Column(String(16))         # 计划完成 yyyy-mm-dd
    duration_days = Column(Float)            # 工期（小时，来自 .mpp Duration）
    work_hours = Column(Float)               # 工时（小时，来自 .mpp Work）
    owner = Column(String(255))              # 负责人/资源（多人顿号分隔）
    percent = Column(Integer, default=0)     # 完成百分比
    wbs = Column(String(64))                 # 任务标识（.mpp WBS）
    outline_number = Column(String(64))      # 大纲编号（.mpp OutlineNumber）
    predecessor = Column(String(64))         # 前置任务
    milestone = Column(String(128))          # 里程碑说明
    seq = Column(Integer, default=0)         # 排序


class SvnModuleSnapshot(Base):
    """SVN 分类同步的模块数据快照（项目方口径：整篇文档提交，但只更新所选类数据，
    其余章节保持文档原样）。module: est(估算)/risk(风险资源)/stake(利益相关方)。
    content 为该模块表格行数据的 JSON 序列化；提交时若未指定该模块则用快照渲染。"""
    __tablename__ = "svn_module_snapshot"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(32), nullable=False)
    module = Column(String(32), nullable=False)      # est / risk / stake
    content = Column(Text(4294967295))               # 行数据 JSON（表格 XML 较大，用 LONGTEXT）
    updated_at = Column(String(32))


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
    """风险（PP/PMC）：A11 软件风险管理表，字段对齐 R121（附录A 项目风险管理表完整 14 列）。"""
    __tablename__ = "risks"
    risk_id = Column(String(64), primary_key=True)
    project_id = Column(String(32), nullable=False, default="R105")
    identified_date = Column(String(32))                # 识别日期，如 2025/10/17
    source = Column(String(32))                         # 风险来源：公司内部/外部/客户/供应商
    category = Column(String(32))                       # 风险类别：人员/技术/需求/计划编制/测试/进度/质量
    description = Column(Text, nullable=False)          # 风险描述（含可能导致的后果+发生时间区间）
    probability = Column(String(16))                    # 概率P 文本：很低/比较低/中等/比较高/很高
    impact_level = Column(String(16))                   # 影响I 文本：很低/比较低/中等/比较高/很高
    risk_coef = Column(String(16))                      # 风险系数 = 概率数值×影响数值（保留小数，自动算）
    level = Column(String(16))                          # 风险等级：低/中/高（自动或手填）
    priority = Column(String(16))                       # 优先级：低/高（自动或手填）
    prevention = Column(Text)                           # 风险预防措施（事前规避）
    owner = Column(String(64))                          # 责任人
    mitigation = Column(Text)                           # 风险应对措施（发生后的处置）
    status = Column(String(16), default="未发生")         # 状态：未发生/已发生/已关闭
    closed_date = Column(String(32))                    # 关闭日期


class Project(Base):
    """项目（当前项目代号等元信息）。支持「新建项目 / 修改项目信息」，全平台代号统一读此表。
    字段覆盖生成开发计划所需的项目关键信息：代号/名称/型号/负责人/单位/阶段/日期/路径。"""
    __tablename__ = "projects"
    project_id = Column(String(32), primary_key=True)    # 项目代号，如 R105（软件编号）
    project_name = Column(String(128))                   # 软件全称，如 R105 飞管软件（-> {{sys.software_full}}）
    aircraft_model = Column(String(64))                  # 飞机型号，如 K409（-> {{sys.short}}）
    owner = Column(String(64))                           # 项目负责人/编制人，如 辛峥峰（-> {{role.author}}/{{org.developer}}）
    org = Column(String(128))                            # 承研单位/开发部门（-> {{org.dev_dept}}）
    customer_dept = Column(String(128))                  # 客户单位（-> {{org.customer_dept}}）
    phase = Column(String(32))                           # 阶段：方案/初样/正样/定型
    start_date = Column(String(32))                      # 立项/开始日期，如 2025-01
    approve_date = Column(String(32))                    # 批准日期（-> {{meta.approve_date}}）
    ide_version = Column(String(64))                     # IDE 版本（-> {{meta.ide_version}}）
    sw_version = Column(String(64))                      # 软件版本示例（-> {{meta.sw_version_example}}）
    doc_number = Column(String(64))                      # 文档编号（可选，覆盖默认 <代号>-SDP）
    local_path = Column(String(255))                     # 默认本机 SVN 工作副本路径
    svn_base_path = Column(String(255))                 # 默认 SVN 基路径
    is_current = Column(Integer, default=0)              # 1=当前项目（平台统一代号来源）
    # ===== SDP 签署角色（A14 共15个签署位，对应 {{role.*}}）=====
    ccb = Column(String(128))                            # 配置控制委员会（CCB）-> {{role.ccb}}
    designer = Column(String(64))                        # 设计者 -> {{role.designer}}
    reviewer = Column(String(64))                        # 评审（主审）-> {{role.reviewer}}
    reviewer2 = Column(String(64))                       # 评审（副审1）-> {{role.reviewer_2}}
    reviewer3 = Column(String(64))                       # 评审（副审2）-> {{role.reviewer_3}}
    tester = Column(String(64))                          # 测试者 -> {{role.tester}}
    qa = Column(String(64))                              # 质量保证（SQA）-> {{role.qa}}
    config_manager = Column(String(64))                  # 配置管理者（CM）-> {{role.config_manager}}
    org_config_manager = Column(String(64))              # 组织级配置管理者 -> {{role.org_config_manager}}
    # ===== 项目组织角色（7.2.1 人力资源 / 相关方清单）=====
    # 三处一致（项目方要求）：前端"新建/修改项目"录入 = 数据库字段 = 生成文档占位符
    requirement = Column(String(64))                     # 需求分析人员 -> {{role.requirement}}
    coder = Column(String(64))                           # 软件实现人员 -> {{role.coder}}
    measure = Column(String(64))                         # 测量分析人员 -> {{role.measure}}
    proj_lead = Column(String(64))                       # 项目负责人 -> {{role.proj_lead}}
    sys_eng = Column(String(64))                         # 系统工程组 -> {{role.sys_eng}}
    # ===== 开发环境（A.4.1 开发环境资源，对应 {{hw.*}}/{{sw.*}}）=====
    hw_ide_name = Column(String(64))                     # 开发工具链名称 -> {{hw.ide_name}}
    hw_mcu_model = Column(String(64))                    # 目标机处理器型号 -> {{hw.mcu_model}}
    sw_name_host = Column(String(128))                   # 宿主软件构件名 -> {{sw.name_host}}
    sw_name_iap = Column(String(128))                    # IAP 软件构件名 -> {{sw.name_iap}}
    # ===== 引用文档（A.2.1 引用文件，对应 {{ref.*}}）=====
    ref_sdtd_doc_number = Column(String(64))            # 软件研制任务书编号 -> {{ref.sdtd_doc_number}}
    ref_sqap_doc_number = Column(String(64))             # 软件质量保证计划编号 -> {{ref.sqap_doc_number}}


class Stakeholder(Base):
    """相关方（PP）：A14。按项目维度隔离。-> {{table.stakeholders}} 相关方清单。"""
    __tablename__ = "stakeholders"
    id = Column(Integer, primary_key=True, autoincrement=True)   # 自增主键
    project_id = Column(String(32), nullable=False, default="R105")  # 项目维度
    role = Column(String(64), nullable=False)
    name = Column(String(64), nullable=False)
    responsibility = Column(Text)
    join_phase = Column(String(32))


class MeetingPlan(Base):
    """会议计划（SDP 会议计划表）：会议类型|会议组织者|会议时机/时间。
    按项目维度隔离。-> {{table.meeting_plan}}
    项目方要求：会议时机不再写死在模板中，改由数据库读取（最优解）；
             数据与"项目策划 - 进度表"中的会议任务保持一致。"""
    __tablename__ = "meeting_plan"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(32), nullable=False, default="R105")
    seq = Column(Integer, nullable=False)          # 序号
    meeting_type = Column(String(128))             # 会议类型
    organizer = Column(String(64))                 # 会议组织者
    timing = Column(String(255))                   # 会议时机/时间


class StakeholderPlan(Base):
    """利益相关方参与计划（对标 R121 附录B）：阶段×活动×9 角色参与矩阵。
    标记：√=计划参与；空=不参与（项目方要求：不再有 ○ 圆圈标记）。
    角色列顺序与 R121 原文一致（9 个）：
    顾客代表 | 项目经理 | 部门领导 | 项目负责人 | 系统工程组 | EPG | QAG | CMG | OTG。"""
    __tablename__ = "stakeholder_plan"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(32), nullable=False, default="R105")
    seq = Column(Integer, nullable=False)
    phase = Column(String(32))
    activity = Column(String(128), nullable=False)
    customer_rep = Column(String(32), default="")   # 顾客代表
    pm = Column(String(32), default="")             # 项目经理
    dept_lead = Column(String(32), default="")      # 部门领导
    proj_lead = Column(String(32), default="")      # 项目负责人
    sys_eng = Column(String(32), default="")        # 系统工程组
    epg = Column(String(32), default="")            # EPG
    qag = Column(String(32), default="")            # QAG
    cmg = Column(String(32), default="")            # CMG
    otg = Column(String(32), default="")            # OTG


class HwRes(Base):
    """硬件资源（PP A.4.1 开发环境资源）：目标机/宿主机/测试设备。
    按项目维度隔离。-> {{table.hw_env_res}} 硬件环境资源表。"""
    __tablename__ = "hw_res"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(32), nullable=False, default="R105")
    name = Column(String(64), nullable=False)     # 资源名称，如 目标机
    spec = Column(String(128))                    # 配置/型号，如 MC9S12X
    usage = Column(String(128))                   # 用途，如 软件加载运行
    owner = Column(String(64))                    # 责任人


class SwRes(Base):
    """软件资源（PP A.4.1 开发环境资源）：宿主机 OS/工具链/测试工具。
    按项目维度隔离。-> {{table.sw_env_res}} 软件环境资源表。"""
    __tablename__ = "sw_res"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(32), nullable=False, default="R105")
    name = Column(String(64), nullable=False)     # 资源名称，如 宿主机操作系统
    spec = Column(String(128))                    # 版本/型号，如 Windows10
    usage = Column(String(128))                   # 用途
    owner = Column(String(64))                    # 责任人


class DocScale(Base):
    """文档规模估算（PP A.3.1 文档规模估计）：各文档类型页数估计。
    按项目维度隔离。-> {{table.doc_scale_est}}/{{table.doc_scale_reuse}} 文档规模估计/复用表。"""
    __tablename__ = "doc_scale"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(32), nullable=False, default="R105")
    code = Column(String(32), nullable=False)     # 文档代号，如 SDP/SRS
    name = Column(String(128), nullable=False)    # 文档名称
    pages_new = Column(Integer, default=0)        # 新开发页数
    pages_reuse = Column(Integer, default=0)      # 复用页数


class CodeScale(Base):
    """代码规模估算（PP A.3.1 代码规模估计）：各构件/模块规模与复用率。
    按项目维度隔离。-> {{table.code_scale_est}}/{{table.code_scale_reuse}} 代码规模估计/复用表。"""
    __tablename__ = "code_scale"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(32), nullable=False, default="R105")
    comp = Column(String(64), nullable=False)      # 构件/模块名，如 飞管主程序
    est_loc = Column(Integer, default=0)          # 预计规模（行）
    reuse_loc = Column(Integer, default=0)        # 复用规模（行）


class TemplateAnchor(Base):
    """模板锚点取值（锚点引擎数据源，兼容 devplan 等模板）。
    支持多项目(project_id)多模板(template_name)并存。
    """
    __tablename__ = "template_anchors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(32), nullable=False, default="R121")
    template_name = Column(String(64), nullable=False)
    anchor_key = Column(String(64), nullable=False)
    anchor_value = Column(MEDIUMTEXT)
    __table_args__ = (
        UniqueConstraint("project_id", "template_name", "anchor_key", name="uk_proj_tpl_anchor"),
    )


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


# ===== SVN 配置（设置页可配，存库，项目方确认）=====
class SvnRepoConfig(Base):
    """SVN 仓库配置（按项目）。统一存库，设置页可配。"""
    __tablename__ = "svn_repo_config"
    project_id = Column(String(32), primary_key=True)     # R121/R105/R120
    repo_url = Column(String(512), nullable=False)        # https://yuanyan/svn/R121/
    username = Column(String(64), default="admin")
    password = Column(String(64), default="123456")
    base_rel_path = Column(String(255), default="trunk/develop")  # 默认开发库


class SvnDocPathMap(Base):
    """文档类型 → SVN 相对路径映射（按项目，可配）。"""
    __tablename__ = "svn_doc_path_map"
    project_id = Column(String(32), primary_key=True)
    template_name = Column(String(64), primary_key=True)  # SDP/SRS...
    rel_path = Column(String(512), nullable=False)        # 如 SDP -> trunk/项目管理/项目策划/项目计划


class LocalSvnPath(Base):
    """本机本地 SVN 路径（machine+user+project 维度，每台机每人不同）。"""
    __tablename__ = "local_svn_path"
    machine_id = Column(String(128), primary_key=True)    # 电脑名+用户
    user_id = Column(String(64), primary_key=True)
    project_id = Column(String(32), primary_key=True)
    local_path = Column(String(512), nullable=False)      # 如 R121 -> D:\5000\R121
