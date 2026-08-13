# -*- coding: utf-8 -*-
"""
基础数据服务（Service 层）
作者：袁燕
功能：组合各 DAO 提供业务门面，事务边界在此层。不含 SQL（SQL 在 DAO）。
      前端/API 通过此类取数，不直接碰 DAO（继承智能柜 P18 分层铁律）。
设计原则：高内聚（业务组合内聚）、低耦合（只依赖 DAO 接口）。
"""
from typing import Optional, Tuple
from backend.dao import requirement_dao, risk_dao, alert_dao, stakeholder_dao, user_dao
from backend.db.models import Requirement, Risk, AlertLog, Stakeholder, User


class DataService:
    """基础数据读写门面"""

    @staticmethod
    def list_requirements(db):
        return requirement_dao.RequirementDao.get_all(db)

    @staticmethod
    def create_requirement(db, req: Requirement):
        return requirement_dao.RequirementDao.create(db, req)

    @staticmethod
    def delete_requirement(db, req_id: str):
        return requirement_dao.RequirementDao.delete(db, req_id)

    @staticmethod
    def list_risks(db):
        return risk_dao.RiskDao.get_all(db)

    @staticmethod
    def create_risk(db, risk: Risk):
        return risk_dao.RiskDao.create(db, risk)

    @staticmethod
    def delete_risk(db, risk_id: str):
        return risk_dao.RiskDao.delete(db, risk_id)

    @staticmethod
    def list_stakeholders(db):
        return stakeholder_dao.StakeholderDao.get_all(db)

    @staticmethod
    def create_stakeholder(db, st: Stakeholder):
        return stakeholder_dao.StakeholderDao.create(db, st)

    @staticmethod
    def delete_stakeholder(db, role: str):
        return stakeholder_dao.StakeholderDao.delete(db, role)

    @staticmethod
    def list_alerts(db, status=None, category=None):
        return alert_dao.AlertDao.get_all(db, status=status, category=category)

    @staticmethod
    def create_alert(db, alert: AlertLog):
        return alert_dao.AlertDao.create(db, alert)

    @staticmethod
    def update_alert_status(db, alert_id: int, status: str):
        obj = alert_dao.AlertDao.get_by_pk(db, alert_id)
        if not obj:
            return None
        obj.status = status
        return alert_dao.AlertDao.update(db, obj)

    # ===== 用户（RBAC）=====
    @staticmethod
    def list_users(db):
        return user_dao.UserDao.get_all(db)

    @staticmethod
    def create_user(db, u: User):
        return user_dao.UserDao.create(db, u)

    @staticmethod
    def delete_user(db, user_id: str):
        return user_dao.UserDao.delete(db, user_id)

    @staticmethod
    def update_user(db, user_id: str, payload: dict):
        """部分更新用户字段。payload 仅含要更新的字段（已转换密码哈希）。返回 User 或 None。"""
        user = user_dao.UserDao.get_by_pk(db, user_id)
        if not user:
            return None
        for k, v in payload.items():
            if v is not None:
                setattr(user, k, v)
        return user_dao.UserDao.update(db, user)

    @staticmethod
    def _hash_password(password: str) -> str:
        """PBKDF2-SHA256 密码哈希（内置 hashlib，无需额外依赖）。"""
        import hashlib, os
        salt = os.urandom(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return salt.hex() + "$" + dk.hex()

    @staticmethod
    def _verify_password(password: str, stored: str) -> bool:
        """校验密码：从 stored 中分离 salt → PBKDF2 验证。"""
        import hashlib
        parts = stored.split("$", 1)
        if len(parts) != 2:
            return False
        salt, dk_stored = bytes.fromhex(parts[0]), parts[1]
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return dk.hex() == dk_stored

    @staticmethod
    def authenticate(db, account: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """
        登录认证：按 account 查用户 → 校验状态 → PBKDF2 校验密码。
        返回 (user, error_msg)：
          - (user, None) 认证成功
          - (None, "账号已被禁用") 用户存在且密码正确但状态为 disabled
          - (None, "账号或密码错误") 账号不存在 / 密码错误 / 其他失败（统一不区分，防枚举）
        """
        user = user_dao.UserDao.get_by_account(db, account)
        if not user:
            return None, "账号或密码错误"
        if not user.password_hash:
            return None, "账号或密码错误"
        if not DataService._verify_password(password, user.password_hash):
            # 密码错误：先判断状态，禁用用户给出不同提示
            if user.state == "disabled":
                return None, "账号已被禁用，请联系管理员"
            return None, "账号或密码错误"
        # 密码正确
        if user.state == "disabled":
            return None, "账号已被禁用，请联系管理员"
        return user, None

    # ===== SVN 集成（提交钩子 + 客户端服务）=====
    @staticmethod
    def save_svn_commit(db, payload) -> "SvnCommitLog":
        """保存 SVN 提交记录。payload 为 SvnCommitIn。返回 ORM 对象。"""
        from backend.db.models import SvnCommitLog
        obj = SvnCommitLog(
            repo_name=payload.repoName,
            commit_user=payload.commitUser,
            revision=payload.revision,
            commit_time=payload.commitTime,
            changed_files=payload.changedFiles,
            project_name=payload.projectName,
            raw_log=payload.rawLog,
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_svn_commits(db, repo: Optional[str] = None) -> list:
        from backend.db.models import SvnCommitLog
        q = db.query(SvnCommitLog)
        if repo:
            q = q.filter(SvnCommitLog.repo_name == repo)
        return q.order_by(SvnCommitLog.id.desc()).limit(200).all()

    @staticmethod
    def mark_affected_watches(db, commit) -> int:
        """
        提交后：找出关注了本次提交仓库/路径的客户端，标记为 pending。
        匹配规则：watch_path 以 repoName 开头（如 R105/trunk/...）。
        返回受影响关注条数。
        """
        from backend.db.models import ClientWatch
        watches = db.query(ClientWatch).filter(
            ClientWatch.watch_path.like(commit.repo_name + "%")
        ).all()
        cnt = 0
        for w in watches:
            # 仅当本次提交版本大于已更新版本才标记待更新
            if commit.revision > w.last_update_rev:
                w.last_update_status = "pending"
                w.last_update_msg = "有新版提交 r%d" % commit.revision
                cnt += 1
        if cnt:
            db.commit()
        return cnt

    @staticmethod
    def upsert_client_watch(db, payload) -> "ClientWatch":
        from backend.db.models import ClientWatch
        exist = db.query(ClientWatch).filter(
            ClientWatch.machine_id == payload.machineId,
            ClientWatch.watch_path == payload.watchPath,
        ).first()
        if exist:
            if payload.userName:
                exist.user_name = payload.userName
            return exist
        obj = ClientWatch(
            machine_id=payload.machineId,
            user_name=payload.userName,
            watch_path=payload.watchPath,
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_client_watches(db, machine: Optional[str] = None) -> list:
        from backend.db.models import ClientWatch
        q = db.query(ClientWatch)
        if machine:
            q = q.filter(ClientWatch.machine_id == machine)
        return q.all()

    @staticmethod
    def get_pending_updates(db, machine_id: str) -> list:
        """
        客户端轮询：返回本机状态为 pending 的关注项。
        每项含 watchId / watchPath / 目标版本(该仓库最新提交版本)。
        返回 [dict, ...] 供 ClientUpdateItem 解析。
        """
        from backend.db.models import ClientWatch, SvnCommitLog
        # pending(有新提交待更新) 或 failed(上次更新失败需重试) 都下发给客户端
        watches = db.query(ClientWatch).filter(
            ClientWatch.machine_id == machine_id,
            ClientWatch.last_update_status.in_(["pending", "failed"]),
        ).all()
        items = []
        for w in watches:
            # 目标版本取该仓库最新提交版本（revision 最大一条）
            repo = w.watch_path.split("/")[0] if w.watch_path else ""
            latest = db.query(SvnCommitLog).filter(
                SvnCommitLog.repo_name == repo
            ).order_by(SvnCommitLog.revision.desc()).first()
            target_rev = latest.revision if latest else w.last_update_rev
            items.append({
                "watchId": w.id,
                "watchPath": w.watch_path,
                "targetRev": target_rev,
            })
        return items

    @staticmethod
    def report_client_update(db, payload) -> bool:
        from backend.db.models import ClientWatch
        w = db.query(ClientWatch).filter(ClientWatch.id == payload.watchId).first()
        if not w:
            return False
        w.last_update_status = payload.status
        if payload.msg:
            w.last_update_msg = payload.msg
        if payload.targetRev:
            w.last_update_rev = payload.targetRev
        db.commit()
        return True
