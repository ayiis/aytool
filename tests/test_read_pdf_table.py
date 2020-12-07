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


def get_image_of_page(page):

    pix = page.getPixmap()
    img_str = pix.getImageData()
    nparr = np.frombuffer(img_str, np.uint8)
    img_np = cv2.imdecode(nparr, 0)

    img_np[img_np < 200] = 0
    img_np[img_np != 0] = 1

    return img_np


import q
import tb1
import cv2
import numpy as np

# doc = fitz.Document("./target.pdf")
doc = fitz.Document("./data/20200324164938兴全趋势投资混合型证券投资基金（LOF）2019年度报告.pdf")
# doc = fitz.Document("./output.2.pdf")
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
        # table_title = "期末按公允价值占基金资产净值比例大小排序的前五名债券投资明细"
        # table_title = "累计卖出金额超出期初基金资产净值"
        table_title = "期末按公允价值占基金资产净值比例大小排序的所有股票投资明细"
        # table_title = "8.5 期末按债券品种分类的债券投资组合"
        search1 = page.searchFor(table_title, hit_max=1)
        if not search1:
            continue
            # raise ValueError("table top delimiter not found")
        rect1 = search1[0]  # the rectangle that surrounds the search string
        ymin = rect1.y1     # table starts below this value
        ymax = 9999

        print("find target string:", ymin, ymax)
        tab = ParseTab(page, [0, ymin, 9999, ymax])

        # 将当前页面图像化
        img_np = get_image_of_page(page)
        page_h, page_w = img_np.shape

        # 剪切出 标题下面的一切
        amin, amax = max(int(ymin + 1), 0), min(img_np.shape[0], 9999)
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

        print("table key points is:", ht_points, wt_points)
        result = tb1.cut_text2(ht_points, wt_points)

        print("\nresult:\n", result)

        # 取当前页的结果
        tab_next = tab
        th_end_next = th_end

        total_result = result

        while "判断跨页":

            pno = pno + 1

            if len(doc) <= pno:
                print("判断跨页：已经达到最后一页")
                break

            table_end_space_rate = ((page_h - th_end_next) / page_h)

            if table_end_space_rate > 0.125:
                print("判断跨页：条件0失败，表格结束点 %s，页面高度 %s，底部空间占比 %s%% > 12.5%%" % (th_end_next, page_h, round(table_end_space_rate * 100, 2)))
                break

            print("判断跨页：条件0成功，表格结束点 %s，页面高度 %s，底部空间占比 %s%% <= 12.5%%" % (th_end_next, page_h, round(table_end_space_rate * 100, 2)))

            # 判断 内容行数不超过2行
            footer_h = 9999

            left_tab_h = [x[1] for x in tab_next if x[1] > th_end_next]
            left_tab_h = sorted(left_tab_h)

            if left_tab_h:

                line_count = 1
                for i in range(len(left_tab_h) - 1):
                    if left_tab_h[i] + 2 < left_tab_h[i + 1]:
                        line_count = line_count + 1

                if line_count > 2:
                    print("判断跨页：条件1失败，页脚内容行数 %s" % (line_count))
                    break

                print("判断跨页：条件1成功，页脚内容行数 %s，高度 %s" % (line_count, footer_h))
                footer_h = left_tab_h[0]

            page_next = doc.loadPage(pno)
            img_np_next = get_image_of_page(page_next)

            tb1.save_png(img_np_next[0:9999], "tmp.next.%s.png" % pno)
            tab_next = ParseTab(page_next, [0, 0, 9999, 9999])

            # 计算表格的 关键点
            tb_point_start_next, tb_point_end_next, ht_points_next, wt_points_next = tb1.detect_table_point(img_np_next[0:9999], 0, 9999, tab_next)

            # 修正计算 点的位置
            ht_points_next = [x + tb_point_start_next[0] + 0 for x in ht_points_next]
            wt_points_next = [x + tb_point_start_next[1] for x in wt_points_next]

            th_start_next = int(tb_point_start_next[0] + 0)
            th_end_next = int(tb_point_end_next[0] + 0)
            tw_start_next = tb_point_start_next[1]
            tw_end_next = tb_point_end_next[1]
            print("th_start: %s, th_end: %s, tw_start: %s, tw_end: %s" % (th_start_next, th_end_next, tw_start_next, tw_end_next))

            if len(wt_points) == len(wt_points_next):

                # 相差 +-2 以内，都算完美匹配
                list_almost_same = all([abs(x - y) < 2 for x, y in zip(wt_points, wt_points_next)])
                if not list_almost_same:
                    print("判断跨页：条件2失败: 后一页的表格的格式不符合：\n%s\n%s" % (wt_points, wt_points_next))
                    break
                else:
                    print("Good!")

                    # 只提取 表格内部 的内容
                    table_content_next = list(filter(lambda x: (th_start_next < x[1] < th_end_next and tw_start_next < x[0] < x[2] < tw_end_next), tab_next))

                    tb1.table_text = table_content_next

                    print("table key points is:", ht_points_next, wt_points_next)
                    result = tb1.cut_text2(ht_points_next, wt_points_next)

                    print("\nresult:\n", result)

                    total_result = np.concatenate([total_result, result])

            else:
                print("判断跨页：条件2失败: 后一页的表格的格式不符合：\n%s\n%s" % (wt_points, wt_points_next))
                break

        print()
        print("\ntotal_result:\n")
        for line in total_result:
            print(line)

        q.d()
        exit()

    except Exception as e:
        print("wtf:", e)
        print(traceback.format_exc())
