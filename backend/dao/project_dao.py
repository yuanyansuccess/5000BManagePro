# -*- coding: utf-8 -*-
"""项目配置 DAO 作者：袁燕
功能：项目（代号/名称/默认路径）增删查改；维护"当前项目"标记。
     平台所有代号（文件名/风险表/路径/SVN）统一读 current_project，杜绝硬编码。
"""
from backend.db.base import BaseDao
from backend.db.models import Project


class ProjectDao(BaseDao):
    model = Project
    pk_field = "project_id"

    @staticmethod
    def get_current(db):
        return db.query(Project).filter(Project.is_current == 1).first()

    @staticmethod
    def ensure_default(db):
        """保证至少存在一个当前项目（首启动兜底：R105）。返回当前项目。"""
        cur = ProjectDao.get_current(db)
        if cur:
            return cur
        # 若无任何项目，建默认 R105 并置为当前
        proj = Project(
            project_id="R105", project_name="R105 软件研制项目",
            local_path="D:/5000/R105", svn_base_path="R105/trunk", is_current=1,
        )
        db.add(proj)
        db.commit()
        db.refresh(proj)
        return proj

    @staticmethod
    def set_current(db, project_id: str):
        """将指定项目置为当前，其余取消当前。返回目标项目或 None。"""
        target = db.query(Project).filter(Project.project_id == project_id).first()
        if not target:
            return None
        for p in db.query(Project).all():
            p.is_current = 1 if p.project_id == project_id else 0
        db.commit()
        return target
