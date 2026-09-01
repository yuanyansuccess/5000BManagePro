# -*- coding: utf-8 -*-
"""代码整改 B 组：空 except 补充安全性说明注释（B1~B4）。作者：袁燕
规范：静默捕获必须写明"为什么静默是安全的"，否则后人无法判断能否删。
"""
import io
import os

BASE = r'D:\5000\5000BManagePro'


def patch(rel, old, new, desc):
    p = os.path.join(BASE, rel)
    src = io.open(p, encoding='utf-8').read()
    if old not in src:
        print(f'  [跳过] {desc}')
        return 0
    io.open(p, 'w', encoding='utf-8').write(src.replace(old, new, 1))
    print(f'  [OK] {desc}')
    return 1


n = 0
# B1 doc.py：告警日志记录失败不阻断 SVN 提交成功响应
n += patch('backend/api/doc.py',
           '        db.commit()\n    except Exception:\n        pass\n',
           '        db.commit()\n'
           '    except Exception:\n'
           '        # 静默安全：SVN 提交本身已成功，告警日志记录失败仅影响审计完整性，\n'
           '        # 不应让前端收到 500（提交结果以 revision 为准）。\n'
           '        pass\n',
           'B1 doc.py 补注释')
# B2 svn_service.py：delete 目标不存在属正常（首次提交前无旧文件）
n += patch('backend/services/svn_service.py',
           '                       capture_output=True, text=True, timeout=60)\n'
           '    except Exception:\n'
           '        pass\n',
           '                       capture_output=True, text=True, timeout=60)\n'
           '    except Exception:\n'
           '        # 静默安全：delete 仅在覆盖旧文件前执行；首次提交时目标不存在属正常。\n'
           '        pass\n',
           'B2 svn_service.py delete 补注释')
# B3 svn_service.py：revision 解析失败保持默认值
n += patch('backend/services/svn_service.py',
           '                except Exception:\n                    pass\n',
           '                except Exception:\n'
           '                    # 静默安全：rev 解析失败时保持默认 0，不影响提交事实。\n'
           '                    pass\n',
           'B3 svn_service.py rev解析 补注释')
# B4 svn_service.py：临时文件清理失败无害
n += patch('backend/services/svn_service.py',
           '            os.remove(local_file)\n            os.rmdir(tmpdir)\n'
           '        except Exception:\n            pass\n',
           '            os.remove(local_file)\n            os.rmdir(tmpdir)\n'
           '        except Exception:\n'
           '            # 静默安全：临时目录清理失败不影响提交结果，留给系统回收。\n'
           '            pass\n',
           'B4 svn_service.py 清理 补注释')
print(f'B 组完成: {n} 条')
