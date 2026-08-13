# -*- coding: utf-8 -*-
"""初始化 MySQL 数据库（作者：袁燕）"""
import pymysql

conn = pymysql.connect(host="127.0.0.1", port=3306, user="root", password="root")
cur = conn.cursor()
cur.execute("CREATE DATABASE IF NOT EXISTS gjb5000b DEFAULT CHARSET utf8mb4")
cur.execute("SHOW DATABASES LIKE 'gjb5000b'")
print("数据库就绪:", cur.fetchone())
conn.commit()
conn.close()
