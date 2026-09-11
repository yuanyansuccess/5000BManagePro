# -*- coding: utf-8 -*-
"""设置项 DAO（SVN 仓库配置 / 文档路径映射 / 本机本地路径）作者：袁燕
功能：三组配置的查询与按业务键 upsert，统一存库（项目方铁律：配置信息不写死代码）。
不含 SQL 之外的逻辑（P18），API 层只调用本 DAO。
"""
from typing import Optional
from sqlalchemy.orm import Session
from backend.db.models import SvnRepoConfig, SvnDocPathMap, LocalSvnPath


class SvnRepoConfigDao:
    model = SvnRepoConfig

    @staticmethod
    def get_all(db: Session):
        return db.query(SvnRepoConfig).order_by(SvnRepoConfig.project_id).all()

    @staticmethod
    def upsert(db: Session, project_id: str, repo_url: str, username: str,
               password: str, base_rel_path: str) -> SvnRepoConfig:
        obj = db.query(SvnRepoConfig).filter(SvnRepoConfig.project_id == project_id).first()
        if not obj:
            obj = SvnRepoConfig(project_id=project_id)
            db.add(obj)
        obj.repo_url = repo_url
        obj.username = username
        obj.password = password
        obj.base_rel_path = base_rel_path
        db.commit()
        return obj


class SvnDocPathMapDao:
    model = SvnDocPathMap
    GLOBAL_PID = "GLOBAL"   # 文档路径映射不分项目（所有项目 SVN 相对路径几乎一致）

    @staticmethod
    def get_all_global(db: Session):
        return db.query(SvnDocPathMap).filter(
            SvnDocPathMap.project_id == SvnDocPathMapDao.GLOBAL_PID
        ).order_by(SvnDocPathMap.template_name).all()

    @staticmethod
    def upsert(db: Session, template_name: str, rel_path: str) -> SvnDocPathMap:
        obj = db.query(SvnDocPathMap).filter(
            SvnDocPathMap.project_id == SvnDocPathMapDao.GLOBAL_PID,
            SvnDocPathMap.template_name == template_name).first()
        if not obj:
            obj = SvnDocPathMap(project_id=SvnDocPathMapDao.GLOBAL_PID, template_name=template_name)
            db.add(obj)
        obj.rel_path = rel_path
        db.commit()
        return obj


class LocalSvnPathDao:
    model = LocalSvnPath

    @staticmethod
    def get_all(db: Session):
        return db.query(LocalSvnPath).order_by(LocalSvnPath.machine_id, LocalSvnPath.user_id).all()

    @staticmethod
    def upsert(db: Session, machine_id: str, user_id: str,
               project_id: str, local_path: str) -> LocalSvnPath:
        obj = db.query(LocalSvnPath).filter(
            LocalSvnPath.machine_id == machine_id, LocalSvnPath.user_id == user_id,
            LocalSvnPath.project_id == project_id).first()
        if not obj:
            obj = LocalSvnPath(machine_id=machine_id, user_id=user_id, project_id=project_id)
            db.add(obj)
        obj.local_path = local_path
        db.commit()
        return obj
