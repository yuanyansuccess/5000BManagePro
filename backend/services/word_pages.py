"""读取 docx 中 PAGEREF 域的真实页号（Word COM 子进程）

袁总 2026-09-04 二次固化（第一轮已修过一次）：用 Word COM 真实打开文档，
对每个 PAGEREF 域取书签所在页号（Information(1) = wdActiveEndPageNumber），
把"目录显示的页码"与"实际页码"对齐，避免 docx XML 缓存的 PAGEREF 与
Word 重新分页后的真实页码不一致。

关键陷阱：
1. Word COM 必须是子进程（uvicorn worker 多进程，COM 不能跨进程复用）。
2. PAGEREF 书签 _TocXXXXX 可能是隐藏书签，必须先 doc.Bookmarks.ShowHidden=True。
3. Information(1) 返回的是"视觉页号"（受 sectPr.pgNumType.start 影响）。
4. 取附录 A 全局页号需要扫描每页首段（不能用段.Range.Information(1)，
   因 start=34 时返回的是节内页号而非全局绝对位置）。
"""
import os
import sys
import json

def main(docx_path: str) -> None:
    import win32com.client as com
    import pythoncom

    out = {
        "docx": docx_path,
        "pages": 0,
        "pagerefs": {},
        "appendix_a_global": None,
        "appendix_a_visual": None,
        "appendix_a_error": None,
        "error": None,
    }
    doc = None
    word = None
    try:
        pythoncom.CoInitialize()
        word = com.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        doc = word.Documents.Open(docx_path, ReadOnly=True)
        doc.Bookmarks.ShowHidden = True
        try:
            doc.Repaginate()
        except Exception:
            pass
        import time
        time.sleep(0.3)
        out["pages"] = int(doc.ComputeStatistics(2))

        # 取每个 PAGEREF 的视觉页号（与 Word 状态栏/页脚 PAGE 域口径一致）
        for f in doc.Fields:
            try:
                code = (f.Code.Text or "").strip()
                if not code.startswith("PAGEREF"):
                    continue
                toks = code.split()
                bm = toks[1] if len(toks) > 1 else ""
                if bm and doc.Bookmarks.Exists(bm):
                    out["pagerefs"][bm] = str(doc.Bookmarks(bm).Range.Information(1))
            except Exception:
                continue

        # 取附录 A 全局页号（Word COM 内部扫描每页首段）
        try:
            total = out["pages"]
            for i in range(1, total + 1):
                rng = doc.GoTo(1, 1, str(i))
                end = doc.GoTo(1, 1, str(i + 1)).Start if i < total else doc.Content.End
                text = doc.Range(rng.Start, min(rng.Start + 100, end)).Text[:80]
                first_line = text.replace("\r", "|").split("|")[0][:30]
                if "附录A" in first_line and "风险管理" in first_line and "目  录" not in text[:30]:
                    out["appendix_a_global"] = i
                    out["appendix_a_visual"] = int(doc.Range(rng.Start, rng.Start).Information(1))
                    break
        except Exception as _e:
            out["appendix_a_error"] = str(_e)[:100]
    except Exception as e:
        out["error"] = str(e)[:200]
    finally:
        try:
            if doc is not None:
                doc.Close(SaveChanges=0)
        except Exception:
            pass
        try:
            if word is not None:
                word.Quit()
        except Exception:
            pass
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass

    print("@@JSON@@")
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: word_pages.py <docx_path>")
        sys.exit(1)
    main(sys.argv[1])