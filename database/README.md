# 数据库初始化脚本

本目录存放 5000B 管理系统使用的 MySQL 数据库 `gjb5000b` 的导出文件（补 2026-09-01 提交时遗漏的数据库部分）。

- `gjb5000b.sql`：由 `mysqldump` 导出的**完整库**（表结构 + 全量业务数据），字符集 utf8mb4。

## 导入方式（本地开发）
```bash[build_manual.py](../build/tools/build_manual.py)
# 1) 建库（若不存在）
mysql --user=root --password=root --host=127.0.0.1 --port=3306 --default-character-set=utf8mb4 -e "CREATE DATABASE IF NOT EXISTS gjb5000b"

# 2) 导入结构与数据
mysql --user=root --password=root --host=127.0.0.1 --port=3306 --default-character-set=utf8mb4 gjb5000b < database/gjb5000b.sql
```

## 导出命令（重新生成时使用）
```bash
mysqldump --user=root --password=root --host=127.0.0.1 --port=3306 ^
  --default-character-set=utf8mb4 --single-transaction --routines --events ^
  --result-file=database/gjb5000b.sql gjb5000b
```

> 说明：连接参数见 `backend/config.py` 的 `DATABASE_URL`（默认 mysql+pymysql://root:root@127.0.0.1:3306/gjb5000b）。
> 本文件含全量业务数据，仅适用于可信的内网/私有仓库部署场景。
[gjb5000b.sql](gjb5000b.sql)