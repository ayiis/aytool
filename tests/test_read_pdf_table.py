#!/usr/bin/python
from operator import itemgetter
from itertools import groupby
import fitz
import traceback


def ParseTab(page, bbox, columns = None):

    tab_rect = fitz.Rect(bbox).irect
    xmin, ymin, xmax, ymax = tuple(tab_rect)

    if tab_rect.isEmpty or tab_rect.isInfinite:
        print("Warning: incorrect rectangle coordinates!")
        return []

    if type(columns) is not list or columns == []:
        coltab = [tab_rect.x0, tab_rect.x1]
    else:
        coltab = sorted(columns)

    if xmin < min(coltab):
        coltab.insert(0, xmin)
    if xmax > coltab[-1]:
        coltab.append(xmax)

    words = page.getTextWords()

    if words == []:
        print("Warning: page contains no text")
        return []

    alltxt = []

    # get words contained in table rectangle and distribute them into columns
    for w in words:
        ir = fitz.Rect(w[:4]).irect          # word rectangle
        if ir in tab_rect:
            cnr = 0                          # column index
            for i in range(1, len(coltab)):  # loop over column coordinates
                if ir.x0 < coltab[i]:        # word start left of column border
                    cnr = i - 1
                    break
            alltxt.append([ir.x0, ir.y0, ir.x1, cnr, w[4]])

    if alltxt == []:
        print("Warning: no text found in rectangle!")
        return []

    return alltxt


import q


doc = fitz.Document("./target.pdf")
# pno = 9
# page = doc.loadPage(pno)

for pno, page in enumerate(doc):

    try:

        #==============================================================================
        # search for top of table
        #==============================================================================
        # table_title = "报告期末按行业分类的境内股票投资组合"
        # table_title = "报告期末基金资产组合情况"
        # table_title = "卖基金份额，受市场供需关系等各种因素的影响"
        # table_title = "主要财务指标"
        # table_title = "本报告期基金份额净值增长率及其与同期业绩比较基准收益率的比较"
        table_title = "任职日期"
        search1 = page.searchFor(table_title, hit_max=1)
        if not search1:
            raise ValueError("table top delimiter not found")
        rect1 = search1[0]  # the rectangle that surrounds the search string
        ymin = rect1.y1     # table starts below this value
        ymax = 99999

        print("find target string:", ymin, ymax)
        # ymin = 43
        tab = ParseTab(page, [0, ymin, 9999, ymax])
        # q.d()

        import cv2
        import numpy as np

        pix = page.getPixmap()
        img_str = pix.getImageData()
        nparr = np.frombuffer(img_str, np.uint8)
        img_np = cv2.imdecode(nparr, 0)

        img_np[img_np < 200] = 0
        img_np[img_np != 0] = 1

        import tb1
        # tb1.table_text = tab[6:]
        # table_h, table_w = tb1.calc_table()
        # tb1.cut_text(table_h, table_w)
        # print("table_h, table_w:", table_h, table_w)

        # tb1.save_png(img_np, "tmp.0.png")

        # 剪切出 标题下面的一切
        amin, amax = max(int(ymin + 1), 0), min(img_np.shape[0], 99999)
        tb1.save_png(img_np[amin:amax], "tmp.1.png")

        # 计算表格的 关键点
        tb_point_start, tb_point_end, ht_points, wt_points = tb1.detect_table_point(img_np[amin:amax], amin, amax, tab)

        # 修正计算 点的位置
        ht_points = [x + tb_point_start[0] + ymin for x in ht_points]
        wt_points = [x + tb_point_start[1] for x in wt_points]

        th_start = int(tb_point_start[0] + ymin)
        th_end = int(tb_point_end[0] + ymin)
        tw_start = tb_point_start[1]
        tw_end = tb_point_end[1]
        print("th_start: %s, th_end: %s, tw_start: %s, tw_end: %s" % (th_start, th_end, tw_start, tw_end))

        # 画出目标区域
        dd = np.zeros(img_np.shape)
        dd[th_start:th_end, tw_start:tw_end] = 1
        tb1.save_png(dd, "tmp.2.png")

        # 只提取 表格内部 的内容
        table_content = list(filter(lambda x: (th_start < x[1] < th_end and tw_start < x[0] < x[2] < tw_end), tab))

        tb1.table_text = table_content
        # q.d()
        print("table key points is:", ht_points, wt_points)

        result = tb1.cut_text2(ht_points, wt_points)

        print("\nresult:\n", result)
        exit()

        #==============================================================================
        # now get the table
        #==============================================================================

        #print(table_title)
        #for t in tab:
        #    print(t)
        # csv = open("p%s.csv" % (pno+1, ), "w")
        # csv.write(table_title + "\n")
        # for t in tab:
        #     csv.write("|".join(t) + "\n")
        # csv.close()
    except Exception as e:
        print("wtf:", e)
        print(traceback.format_exc())
