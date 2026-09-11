# -*- coding: utf-8 -*-
"""
R105 真实数据预置（数据源：D:/5000/R105/项目管理/项目策划/项目计划/软件开发计划V3.01.docx）。
作者：袁燕
功能：把 R105 开发计划中的真实业务数据（风险/文档规模/代码规模/工作量进度/利益相关方/
      硬件资源/软件资源/项目签署角色）一次性填充数据库，供生成开发计划与前端展示。
      重复执行安全（先清后插，按项目维度隔离）。
"""
import sys
sys.path.insert(0, 'd:/5000/5000BManagePro')

from backend.db.session import SessionLocal, Engine
from backend.db.models import (Project, Risk, DocScale, CodeScale,
                               SchedulePhase, StakeholderPlan, HwRes, SwRes,
                               ProjectMember, Base)

PID = "R105"

# ---- 风险（附录A 4 条真实风险，责任人 辛峥峰）----
RISKS = [
    dict(identified_date="2024-4-29", source="公司内部", category="人员风险",
         description="关键人员因其它项目影响或自身原因可能不能按计划参与项目软件活动",
         probability="比较低", impact_level="比较低", risk_coef="0.8", level="低", priority="低",
         prevention="保持与项目组成员的沟通，及时了解关键人员当前工作任务情况，协调与其它工作任务的进度安排",
         owner="辛峥峰", mitigation="提请部门领导协调人员；补充人员", status="未发生", closed_date=""),
    dict(identified_date="2024-4-29", source="公司内部", category="测试相关风险",
         description="测试所需要的测试工具未及时到位，导致测试工作无法按期进行",
         probability="比较低", impact_level="比较低", risk_coef="0.8", level="低", priority="低",
         prevention="保持与系统组沟通，定期跟踪测试设备的使用状态，协调测试设备的投入使用的时间，避免与其它项目使用该设备的时间发生冲突。",
         owner="辛峥峰", mitigation="提请部门领导协调备用设备或相同功能的设备及时投入本项目，满足项目测试需要。", status="未发生", closed_date=""),
    dict(identified_date="2024-4-29", source="公司内部", category="需求风险",
         description="项目需求未定，可能需求反复变更影响交付质量。",
         probability="比较低", impact_level="中等", risk_coef="1.2", level="中", priority="高",
         prevention="保持与系统组沟通，及时了解用户使用场景和隐藏需求；对确定的需求进行技术评审，确定需求的有效性和合理性；",
         owner="辛峥峰", mitigation="针对需求变更，增加人员专职投入，邀请部门领导专家参与影响分析，和验证归零。", status="未发生", closed_date=""),
    dict(identified_date="2024-4-29", source="公司内部", category="计划编制风险",
         description="项目可能未按计划进行，阶段任务进度严重滞后，超出阈值，导致项目无法按期交付。",
         probability="比较低", impact_level="比较高", risk_coef="1.6", level="中", priority="高",
         prevention="双周监控任务完成进度，分析监控异常情况，及时调整工作安排。",
         owner="辛峥峰", mitigation="当出现偏差时分析任务是否处于关键路径，分析偏差原因，当资源不满足时提请部门领导协调资源（人力、物力）；当技术原因时组织专家参与问题分析和解决。", status="未发生", closed_date=""),
]

# ---- 文档规模（18 个文档，总计 293 页；代号对标 R105 表11 配置项标识 + _V1.00 版本后缀）----
DOC_SCALE = [
    ("R105_SDP_V1.00", "软件开发计划", 37, ""),
    ("R105_SQAP_V1.00", "软件质量保证计划", 12, ""),
    ("R105_0201_SRS_V1.00", "R105_0201软件需求规格说明", 21, "触摸屏控制软件"),
    ("R105_0202_SRS_V1.00", "R105_0202软件需求规格说明", 19, "主控板控制软件"),
    ("R105_0201_SDD_V1.00", "R105_0201软件设计说明", 22, "触摸屏控制软件"),
    ("R105_0202_SDD_V1.00", "R105_0202软件设计说明", 20, "主控板控制软件"),
    ("R105_SSTP_V1.00", "软件测试计划", 18, ""),
    ("R105_0201_CSTD_V1.00", "R105_0201软件配置项测试说明", 20, "触摸屏控制软件"),
    ("R105_0202_CSTD_V1.00", "R105_0202软件配置项测试说明", 18, "主控板控制软件"),
    ("R105_0201_CSTR_V1.00", "R105_0201软件配置项测试报告", 20, "触摸屏控制软件"),
    ("R105_0202_CSTR_V1.00", "R105_0202软件配置项测试报告", 18, "主控板控制软件"),
    ("R105_SSTD_V1.00", "软件系统测试说明", 22, ""),
    ("R105_SSTR_V1.00", "软件系统测试报告", 25, ""),
    ("R105_SPS_V1.00", "软件产品规格说明", 4, ""),
    ("R105_SVD_V1.00", "软件版本说明", 3, ""),
    ("R105_SUM_V1.00", "软件用户手册", 4, ""),
    ("R105_FSM_V1.00", "软件固件保障手册", 4, ""),
    ("R105_SDSR_V1.00", "软件研制工作总结", 10, ""),
]

# ---- 代码规模（估算单元=2 个软件配置项，对标 R105 表：触摸屏 505 / 主控板 516）----
CODE_SCALE = [
    ("触摸屏控制软件", 505),
    ("主控板控制软件", 516),
]

# ---- 工作量估算/进度（7 阶段：项目启动+项目策划 0 工作量标识时间窗 + 5 实施阶段）----
# 与 scripts/fill_phases_r105.py 保持一致
SCHEDULE = [
    (1, "项目启动", "0%", 0.0, 0.0, "2024-04-05", "2024-04-22", "项目启动会议（2024-4-5）"),
    (2, "项目策划", "0%", 0.0, 0.0, "2024-04-23", "2024-04-30", "软件项目计划评审会议（2024-4-29）"),
    (3, "需求", "19%", 8.721, 5.814, "2024-05-01", "2024-05-15", "软件需求规格说明技术评审（2024-5-15）"),
    (4, "设计", "24%", 11.016, 7.344, "2024-05-16", "2024-06-14", "软件设计说明签字审批（2024-5-30）"),
    (5, "实现", "29%", 13.311, 8.874, "2024-05-16", "2024-06-14", "软件源代码签字审批（2024-6-14）"),
    (6, "测试", "22%", 10.098, 6.732, "2024-06-15", "2024-06-30", "软件测试报告技术评审（2024-6-30）"),
    (7, "验收", "6%", 2.754, 1.836, "2024-07-01", "2024-07-05", "项目结项（2024-7-5）"),
]

# 注：利益相关方参与计划（16 角色）已由 scripts/seed_r105_stake.py 专项管理，
#     本脚本不再处理（避免字段不一致导致整个 seed 崩溃、后续数据未写入）。

# ---- 硬件/外部资源（R105 表31，6 条）----
HW_RES = [
    ("工业计算机", "搭建开发环境", "可以运行集成开发环境和测试软件", "公司现有", "——"),
    ("RS232数据通信卡", "搭建开发环境", "通道数：1ch", "公司现有", "2024-6-1"),
    ("万用表", "搭建开发环境", "测量输出信号通断", "公司现有", "2024-6-1"),
    ("终点/轮载开关模拟器", "搭建测试环境", "含有功能正常的液晶触摸屏和主控板", "系统组提供", "2024-6-1"),
    ("通用计算机", "搭建测试环境", "操作系统windows7 / 内存32GB，硬盘2T", "系统组提供", "2024-6-1"),
    ("仿真器", "代码写入和系统单步调试", "型号：GD-Link", "系统组提供", "2024-6-1"),
]

# ---- 软件资源（R105 表32，6 条）----
SW_RES = [
    ("Keil 4", "集成开发环境", "软件开发", "现有", "——"),
    ("MS Office2007", "文档处理", "软件开发", "现有", "——"),
    ("SourceInsight 4.0", "代码检视", "软件代码统计", "现有", "——"),
    ("DWIN DGUS_V7641", "界面设计", "软件开发", "现有", "——"),
    ("Windows 7", "操作系统", "软件运行环境", "现有", "——"),
    ("串口通讯助手V1.0", "调试、测试", "软件开发、测试", "现有", "——"),
]


def main():
    # 建表（幂等）：全部业务表（防表缺失，如 migrate 残留半成品时）
    from backend.db.models import StakeholderPlan as _SP  # noqa 确保模型已加载
    Base.metadata.create_all(Engine)
    db = SessionLocal()
    try:
        # 1) 项目元信息（R105 真实：项目名/签署角色/开发环境）
        proj = db.query(Project).filter(Project.project_id == PID).first()
        if proj:
            proj.project_name = "终点/轮载开关模拟器驱动软件"
            proj.ccb = "许宏刚"
            proj.org_config_manager = "廖建英"
            proj.config_manager = "张星竹"
            proj.owner = "辛峥峰"
            proj.qa = "杜晟"
            proj.designer = "吴明森、罗臻"
            proj.tester = "谢柯薪"
            proj.ide_version = "Keil 4"
            proj.hw_ide_name = "Keil 4"
            proj.sw_name_host = "触摸屏控制软件"
            proj.sw_name_iap = "主控板控制软件"
            proj.local_path = proj.local_path or "D:/5000/R105"
            proj.svn_base_path = proj.svn_base_path or "R105/trunk"

        # 2) 风险（先清后插）
        db.query(Risk).filter(Risk.project_id == PID).delete(synchronize_session=False)
        for i, rk in enumerate(RISKS, start=1):
            db.add(Risk(project_id=PID, risk_id=str(i), **rk))

        # 3) 文档规模
        db.query(DocScale).filter(DocScale.project_id == PID).delete(synchronize_session=False)
        for code, name, pages, note in DOC_SCALE:
            db.add(DocScale(project_id=PID, code=code, name=name,
                            pages_new=pages, pages_reuse=0))

        # 4) 代码规模（估算单元）
        db.query(CodeScale).filter(CodeScale.project_id == PID).delete(synchronize_session=False)
        for comp, loc in CODE_SCALE:
            db.add(CodeScale(project_id=PID, comp=comp, est_loc=loc, reuse_loc=0))

        # 5) 工作量/进度
        db.query(SchedulePhase).filter(SchedulePhase.project_id == PID).delete(synchronize_session=False)
        for no, name, ratio, eng, mgr, sd, ed, adj in SCHEDULE:
            db.add(SchedulePhase(project_id=PID, phase_no=no, phase_name=name,
                                 ratio=ratio, eng_md=eng, mgr_md=mgr,
                                 start_date=sd, end_date=ed, milestone=adj))

        # 6) 利益相关方参与计划 -> 由 scripts/seed_r105_stake.py 专项管理（此处不处理）

        # 7) 硬件/软件资源（字段映射：spec=指标要求/功能要求，owner=来源/提供方）
        db.query(HwRes).filter(HwRes.project_id == PID).delete(synchronize_session=False)
        for name, use, spec, src, date in HW_RES:
            db.add(HwRes(project_id=PID, name=name, usage=use, spec=spec, owner=src))
        db.query(SwRes).filter(SwRes.project_id == PID).delete(synchronize_session=False)
        for name, use, req, src, date in SW_RES:
            db.add(SwRes(project_id=PID, name=name, usage=use, spec=req, owner=src))

        # 8) 项目人员（R105 真实名册，文档签署/角色分配基础）
        db.query(ProjectMember).filter(ProjectMember.project_id == PID).delete(synchronize_session=False)
        MEMBERS = [
            ("辛峥峰", "软件负责人", "软件", "SF-01", "svn://pdm/R105/辛峥峰", "全部"),
            ("马慧芳", "需求", "软件", "MF-02", "svn://pdm/R105/马慧芳", "需求/文档"),
            ("吴明森", "设计实现", "设计", "WM-03", "svn://pdm/R105/吴明森", "设计/编码"),
            ("罗臻", "设计实现", "设计", "LZ-04", "svn://pdm/R105/罗臻", "设计/测试"),
            ("谢柯薪", "测试", "测试", "XK-05", "svn://pdm/R105/谢柯薪", "测试/验证"),
            ("杜晟", "QA", "质保", "DS-06", "svn://pdm/R105/杜晟", "质量保证"),
            ("张星竹", "配置管理员", "配置", "ZX-07", "svn://pdm/R105/张星竹", "配置管理"),
            ("许宏刚", "CCB", "管理", "XG-08", "svn://pdm/R105/许宏刚", "变更审批"),
        ]
        for i, (nm, role, team, no, svn, auth) in enumerate(MEMBERS, start=1):
            db.add(ProjectMember(project_id=PID, name=nm, role=role, team=team,
                                 no=no, svn=svn, auth=auth, seq=i))

        db.commit()
        # 注：相关方由 scripts/seed_r105_stake.py 专项预置，此处不统计
        print("[OK] R105 真实数据预置完成：风险%d 文档规模%d 代码规模%d 进度%d 硬件%d 软件%d 人员%d"
              % (len(RISKS), len(DOC_SCALE), len(CODE_SCALE), len(SCHEDULE),
                 len(HW_RES), len(SW_RES), 8))
    except Exception as e:
        db.rollback()
        print("[FAIL]", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
