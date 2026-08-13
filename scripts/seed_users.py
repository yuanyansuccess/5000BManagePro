# -*- coding: utf-8 -*-
"""
种子数据脚本：向 gjb5000b 数据库灌入初始用户（含 PBKDF2 密码哈希）。
作者：袁燕
功能：首次部署 / 数据库重建后执行，创建平台默认用户。
用法：python scripts/seed_users.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.session import Engine, SessionLocal, init_db
from backend.db.models import User
from backend.services.data_service import DataService

# 先建表
init_db()

db = SessionLocal()

# 默认用户清单（对标 R105 项目实际名册）
USERS = [
    {"user_id": "U001", "name": "辛峥峰", "account": "xin.zhengfeng",  "password": "123456", "role": "admin", "auth_list": "all"},
    {"user_id": "U002", "name": "马慧芳",   "account": "ma.huifang",    "password": "123456", "role": "user",  "auth_list": ""},
    {"user_id": "U003", "name": "吴明森",   "account": "wu.mingsen",    "password": "123456", "role": "user",  "auth_list": ""},
    {"user_id": "U004", "name": "罗臻",     "account": "luo.zhen",      "password": "123456", "role": "user",  "auth_list": ""},
    {"user_id": "U005", "name": "谢柯薪",   "account": "xie.kexin",     "password": "123456", "role": "user",  "auth_list": ""},
    {"user_id": "U006", "name": "张星竹",   "account": "zhang.xingzhu", "password": "123456", "role": "user",  "auth_list": ""},
    {"user_id": "U007", "name": "杜晟",     "account": "du.sheng",      "password": "123456", "role": "user",  "auth_list": ""},
    {"user_id": "U008", "name": "孙超",     "account": "sun.chao",      "password": "123456", "role": "user",  "auth_list": ""},
    {"user_id": "U009", "name": "张莉",     "account": "zhang.li",      "password": "123456", "role": "user",  "auth_list": ""},
    {"user_id": "U010", "name": "许宏刚",   "account": "xu.honggang",   "password": "123456", "role": "user",  "auth_list": ""},
    {"user_id": "U011", "name": "廖建英",   "account": "liao.jianying", "password": "123456", "role": "user",  "auth_list": ""},
]

try:
    created = 0
    for u in USERS:
        existing = db.query(User).filter(User.account == u["account"]).first()
        if existing:
            print(f"[跳过] {u['name']} ({u['account']}) 已存在")
            continue
        obj = User(
            user_id=u["user_id"],
            name=u["name"],
            account=u["account"],
            password_hash=DataService._hash_password(u["password"]),
            role=u["role"],
            auth_list=u.get("auth_list", ""),
            state="active",
        )
        db.add(obj)
        created += 1
        print(f"[创建] {u['name']} ({u['account']})")
    db.commit()
    print(f"\n完成：创建 {created} 个新用户，跳过 {len(USERS) - created} 个已存在用户。")
except Exception as e:
    db.rollback()
    print(f"[错误] {e}")
finally:
    db.close()
