# -*- coding: utf-8 -*-
"""检查各动态表格的 gridCol 与总宽是否适配所在页（纵向/横向）。作者：袁燕"""
import re
import sys

sys.path.insert(0, 'd:/5000/5000BManagePro')

from backend.db.session import SessionLocal  # noqa: E402
from backend.db.models import (DocScale, HwRes, SwRes, Stakeholder,  # noqa: E402
                               SchedulePhase, Project)
from backend.services.table_builder import (  # noqa: E402
    build_doc_scale_tbl, build_hw_env_tbl, build_sw_env_tbl,
    build_stakeholders_tbl, build_code_scale_tbl, build_schedule_tbl,
    build_risks_tbl, build_data_mgmt_tbl)

LIMIT_PORTRAIT = 9468
LIMIT_LANDSCAPE = 14406


def show(name, xml, limit, zone):
    grid = [int(x) for x in re.findall(r'<w:gridCol w:w="(\d+)"/>', xml)]
    total = sum(grid)
    ok = 'OK' if total <= limit else f'溢出+{total - limit}'
    print(f'{name:20} 列{len(grid)} 合计={total:6} 上限={limit}({zone}) {ok}')
    return total <= limit


def main():
    db = SessionLocal()
    try:
        docs = db.query(DocScale).filter(DocScale.project_id == 'R105').all()
        hw = db.query(HwRes).filter(HwRes.project_id == 'R105').all()
        sw = db.query(SwRes).filter(SwRes.project_id == 'R105').all()
        st = db.query(Stakeholder).filter(Stakeholder.project_id == 'R105').all()
        ph = db.query(SchedulePhase).filter(SchedulePhase.project_id == 'R105').all()
        proj = db.query(Project).filter(Project.project_id == 'R105').first()
    finally:
        db.close()

    print('--- 纵向节（正文）---')
    r = [
        show('doc_scale_est', build_doc_scale_tbl(docs, kind='est'), LIMIT_PORTRAIT, '纵向'),
        show('doc_scale_reuse', build_doc_scale_tbl(docs, kind='reuse'), LIMIT_PORTRAIT, '纵向'),
        show('code_scale_est', build_code_scale_tbl('R105'), LIMIT_PORTRAIT, '纵向'),
        show('code_scale_reuse', build_code_scale_tbl('R105', kind='reuse'), LIMIT_PORTRAIT, '纵向'),
        show('stakeholders', build_stakeholders_tbl(st), LIMIT_PORTRAIT, '纵向'),
        show('schedule', build_schedule_tbl(ph), LIMIT_PORTRAIT, '纵向'),
        show('hw_env_res', build_hw_env_tbl(hw), LIMIT_PORTRAIT, '纵向'),
        show('sw_env_res', build_sw_env_tbl(sw), LIMIT_PORTRAIT, '纵向'),
    ]
    print('--- 横向节（附录）---')
    r.append(show('risks', build_risks_tbl('R105'), LIMIT_LANDSCAPE, '横向'))
    r.append(show('data_mgmt', build_data_mgmt_tbl(proj), LIMIT_LANDSCAPE, '横向'))
    print()
    print('全部通过' if all(r) else '存在溢出，需继续调整')


if __name__ == '__main__':
    main()
