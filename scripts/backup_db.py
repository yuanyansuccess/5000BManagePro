# -*- coding: utf-8 -*-
"""数据库全量备份（mysqldump）。作者：袁燕
用途：代码整改/提交前的安全兜底（袁总指示）。
输出：backup/db_backup_YYYYMMDD_HHMMSS.sql
"""
import glob
import os
import re
import subprocess
from datetime import datetime

import sys
sys.path.insert(0, 'd:/5000/5000BManagePro')

from backend import config

BASE_DIR = config.BASE_DIR
DB_URL = config.DATABASE_URL


def main():
    m = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^:/]+):(\d+)/(\w+)', DB_URL)
    if not m:
        print('[FAIL] 无法解析数据库连接串')
        return
    user, pwd, host, port, dbname = m.groups()

    out_dir = os.path.join(BASE_DIR, 'backup')
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out = os.path.join(out_dir, f'db_backup_{stamp}.sql')

    # 定位 mysqldump（常见安装位置；找不到则用 PATH）
    cmd_base = 'mysqldump'
    for c in (glob.glob(r'C:\Program Files\MySQL\MySQL Server *\bin\mysqldump.exe')
              + glob.glob(r'C:\Program Files\MySQL\*\bin\mysqldump.exe')
              + glob.glob(r'D:\**\bin\mysqldump.exe', recursive=True)):
        if os.path.exists(c):
            cmd_base = c
            break

    cmd = [cmd_base, '-h' + host, '-P' + port, '-u' + user, '-p' + pwd,
           '--default-character-set=utf8mb4', '--single-transaction', dbname]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        print('[FAIL]', r.stderr.decode('gbk', errors='ignore')[:400])
        return
    content = r.stdout.decode('utf-8', errors='ignore')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(content)
    size = os.path.getsize(out)
    if size < 500:
        print('[FAIL] 备份文件过小:', content[:200])
        return
    print(f'[OK] 备份完成: {out}  ({size/1024:.1f} KB)')

    manifest = os.path.join(out_dir, 'README.txt')
    with open(manifest, 'a', encoding='utf-8') as f:
        f.write(f'{datetime.now():%Y-%m-%d %H:%M:%S}  {os.path.basename(out)}  '
                f'{size/1024:.1f} KB  db={dbname}\n')
    print('备份清单已更新:', manifest)


if __name__ == '__main__':
    main()
