# -*- coding: utf-8 -*-
"""清理 projects 表中的示例假名（张三/李四/赵六/钱七/孙八等），并按 R105 真实人员
补齐"项目组织角色"五个新字段。作者：袁燕

袁总反馈："赵六从未出现在文档中"、"钱七、孙八显示为软件实现人员"、
        "需求分析人员应该在修改项目/新建项目中，李维不应该写死在文档中"。
经核对：reviewer=赵六、reviewer2=钱七、reviewer3=孙八 均为模板示例假名（非真实人员），
       且此前被错位填进了"项目负责人""软件实现"等位置。

处理：
  1) 清除所有常见示例假名（置空），由袁总在"修改项目"中补填真实人员；
  2) 按 R105 真实数据补齐五个新角色字段（避免生成文档留空）：
     requirement 需求分析人员 = 马慧芳
     coder       软件实现人员 = 吴明森、罗臻
     measure     测量分析人员 = 张星竹
     proj_lead   项目负责人   = 孙超
     sys_eng     系统工程组   = 孙超
     （数据源 R105 软件开发计划V3.01 表29/表30；仅填空值，不覆盖已有值）
"""
import sys

sys.path.insert(0, 'd:/5000/5000BManagePro')

from backend.db.session import SessionLocal  # noqa: E402
from backend.db.models import Project  # noqa: E402

# 常见中文示例假名
FAKE_NAMES = ['张三', '李四', '王五', '赵六', '钱七', '孙八', '周九', '吴十',
              '某某', 'XXX', 'xxx']

ROLE_COLS = ['ccb', 'org_config_manager', 'designer', 'reviewer', 'reviewer2',
             'reviewer3', 'tester', 'qa', 'config_manager', 'owner',
             'requirement', 'coder', 'measure', 'proj_lead', 'sys_eng']

# R105 真实人员（数据源：R105 软件开发计划V3.01 表29 组织机构 / 表30 人力资源）
R105_ROLES = {
    'requirement': '马慧芳',
    'coder': '吴明森、罗臻',
    'measure': '张星竹',
    'proj_lead': '孙超',
    'sys_eng': '孙超',
}


def main():
    db = SessionLocal()
    try:
        for p in db.query(Project).all():
            print(f'--- 项目 {p.project_id} {p.project_name}')
            for col in ROLE_COLS:
                v = getattr(p, col) or ''
                hit = [n for n in FAKE_NAMES if n in v]
                if hit:
                    print(f'    清理 {col}: {v!r} -> "" （命中假名 {hit}）')
                    setattr(p, col, '')
            for col, val in R105_ROLES.items():
                cur = getattr(p, col) or ''
                if not cur.strip():
                    setattr(p, col, val)
                    print(f'    补填 {col} = {val}')
        db.commit()
        print()
        print('=== 最终角色值 ===')
        for p in db.query(Project).all():
            print(f'  [{p.project_id}]')
            for c in ROLE_COLS:
                print(f'    {c:20} = {getattr(p, c)}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
