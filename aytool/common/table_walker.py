"""
    1. 搜索 title，按照 title 位置，从下方开始定位表格

    ✅
        + 支持 简单十字结构 的表格
        + 支持 翻页 的表格

    ⛔️
        - 同一行只能出现 1 个表格
        - 不支持虚线或者富格式，内多行的表格
"""
import re

import q
import numpy as np
import cv2
import fitz
from sympy import symbols, solve


class Walker(object):

    PADDING_HEIGHT = 2  # 通用字符间隔，通过字符尺寸计算得出
    PAGE_MAX_SIZE = 9999
    DEBUG = True
    # magic number
    ALMOST_ALL = 0.968
    TEXT_GRAY = 218     # 字体和表格线的灰度（注意表头有时候会存在灰色背景） < TEXT_GRAY

    def __init__(self, pdf_file, debug=False, text_gray=218):
        super(Walker, self).__init__()
        self.pdf_file = pdf_file
        self.pdf = fitz.Document(pdf_file)
        self.page_count = len(self.pdf)
        self.DEBUG = debug
        self.TEXT_GRAY = text_gray

    def find_main_title(self):
        """
            pdf 的主标题，应该出现在前3页，字体应该最大
        """
        for page_no in range(3):
            page = self.pdf.loadPage(page_no)
            page_texts = page.getTextWords()
            if not page_texts:
                continue

            text_list = []
            for text in page_texts:
                text_list.append([text[1], text[3], text[3] - text[1], text[4]])

            sorted_text = sorted(text_list, key=lambda x: -x[2])
            height_end, max_height = sorted_text[0][1], sorted_text[0][2]
            filter_text = filter(lambda x: max_height - x[2] <= self.PADDING_HEIGHT and x[0] <= height_end + max_height, text_list)
            return " ".join([x[3] for x in filter_text])

    def get_text_line(self, text_list):
        """
            text_list 里的任意一个被匹配到，则返回当前行的内容
            # 如果需要，可以改成 生成器
        """
        for page_no in range(self.page_count):

            page = self.pdf.loadPage(page_no)
            for title in text_list:

                page_texts = page.getTextWords()
                match_line = next((t for t in page_texts if title in t[4]), None)
                if not match_line:
                    continue

                center = (match_line[3] + match_line[1]) / 2
                fix = (match_line[3] - match_line[1]) / 2

                line = [t for t in page_texts if abs((t[3] + t[1]) / 2 - center) < fix]
                line = sorted(line, key=lambda x: x[0])

                line_text = "".join([t[4] for t in line])

                return line_text

        return None

    def get_rect_text(self, page, rect):

        tab_rect = fitz.Rect(rect).irect

        if tab_rect.isEmpty or tab_rect.isInfinite:
            self.print("Warning: incorrect rectangle coordinates!")
            return []

        words = page.getTextWords()

        if not words:
            self.print("Warning: page contains no text")
            return []

        # 根据 高度 筛选
        alltxt = [w[:5] for w in words if rect[1] <= w[1] <= rect[3]]

        if not alltxt:
            self.print("Warning: no text found in rectangle!")
            return []

        return alltxt

    def print(self, *args):
        if self.DEBUG:
            print(*args)

    def get_snapshot(self, page):

        img_buf = page.getPixmap()
        img_data = img_buf.getImageData()
        nparr = np.frombuffer(img_data, np.uint8)
        img_np = cv2.imdecode(nparr, 0)

        # 有点遗憾，这个切割方法并不精确
        img_np[img_np < self.TEXT_GRAY] = 0
        img_np[img_np != 0] = 1

        return img_np

    def save_process_image(self, np_binary, save_path):
        if self.DEBUG:
            self.print("Save to:", save_path)
            _, imth = cv2.threshold(np_binary, 0, 255, cv2.THRESH_BINARY)
            cv2.imwrite(save_path, imth)

    def calc_continue_point(self, tf_list):

        w_cut = 0
        w_cut_pare = []
        # 统计连续的 False (存在字符)
        for i in range(len(tf_list)):
            if not tf_list[i]:
                w_cut += 1
            else:
                if w_cut:
                    w_cut_pare.append((i - w_cut, i, w_cut))
                    w_cut = 0

        if w_cut != 0:
            w_cut_pare.append((i - w_cut, i, w_cut))

        return w_cut_pare

    def sym_calc(self, cond_list):
        x, y = symbols("x y")

        if len(cond_list) == 1:
            cond = cond_list[0]
            if cond[1] == 0:
                result = solve(x * cond[0] - cond[2], x)
                x, y = result[0], result[0] / 2
            elif cond[0] == 0:
                result = solve(y * cond[1] - cond[2], y)
                x, y = result[0] * 2, result[0]
            else:
                result = solve([
                    x * cond[0] + y * cond[1] - cond[2],
                    x - 2 * y,
                ], [x, y])
                x, y = result.values()
        else:
            cond0 = cond_list[0]
            cond1 = cond_list[1]
            result = solve([
                x * cond0[0] + y * cond0[1] - cond0[2],
                x * cond1[0] + y * cond1[1] - cond1[2],
            ], [x, y])
            x, y = result.values()

        return float(x), float(y)

    def calc_char_len(self, text):
        """
            只要有 2 个不同长度的字符串，就可以计算出正确的字体的尺寸
        """
        calc_list = []

        for line in text:
            list_char = line[4]
            list_len = line[2] - line[0]
            if list_char:
                calc_list.append((list_char, list_len))

        got_de, got_chr = False, False
        cond_list = []
        for item in calc_list:

            count_de = len(re.findall(r"""[a-z_A-Z0-9-\.!@#\$%\\\^&\*\)\(\+=\{\}\[\]\/",'<>~\·`\?:;|]""", item[0]))
            count_chr = len(item[0]) - count_de

            # 2个 未知数 才能解方程
            if not (count_de and count_chr):
                if not count_de:
                    if got_chr:
                        continue
                    else:
                        got_chr = True

                if not count_chr:
                    if got_de:
                        continue
                    else:
                        got_de = True
            else:
                got_de, got_chr = True, True

            cond_list.append((count_chr, count_de, item[1]))
            if len(cond_list) > 1:
                break

        if not cond_list:
            return 0, 0

        size_chr, size_de = self.sym_calc(cond_list)

        self.PADDING_HEIGHT = max(self.PADDING_HEIGHT, round(size_de / 2))
        self.print("size_chr: %s, size_de: %s, self.PADDING_HEIGHT: %s" % (round(size_chr, 2), round(size_de, 2), self.PADDING_HEIGHT))

        return size_chr, size_de

    def np_almost_all_is1(self, np_list):
        return np_list.sum() / np_list.size > self.ALMOST_ALL

    def np_almost_all_is0(self, np_list):
        return np_list.sum() / np_list.size < 1 - self.ALMOST_ALL

    def fix_zip_cut_points(self, dn, p_cut_start, p_cut_end):
        """
            裁剪 表格外的内容
            裁剪 表格线向外逃逸的 0
        """
        total_time = (p_cut_end[1] - p_cut_start[1]) * (p_cut_end[0] - p_cut_start[0])

        # 从4个方向逼近，直到不能再逼近为止
        for i in range(total_time):

            same = True

            tn = dn[p_cut_start[0]:p_cut_end[0], p_cut_start[1]:p_cut_end[1]]
            ht, wt = tn.shape

            zh, fh = None, None
            # 从前往后
            for h in range(ht - 1):
                # 必然有几乎全是 0 的行
                if self.np_almost_all_is0(tn[h]):
                    break
                else:
                    same = False
                    zh = h
            else:
                # 没有几乎全 0 的行
                return False

            if zh is not None:
                p_cut_start[0] = p_cut_start[0] + zh + 1
                continue

            # 从后往前
            for h in range(ht):
                # 必然有几乎全是 0 的行
                if self.np_almost_all_is0(tn[ht - 1 - h]):
                    break
                else:
                    same = False
                    fh = h
            else:
                # 没有几乎全 0 的行
                return False

            if fh is not None:
                p_cut_end[0] = p_cut_end[0] - fh - 1
                continue

            zw, fw = None, None
            # 从前往后
            for w in range(wt - 1):
                # 必然有几乎全是 0 的行
                if self.np_almost_all_is0(tn[:, w]):
                    break
                else:
                    same = False
                    zw = w
            else:
                # 没有几乎全 0 的行
                return False

            if zw is not None:
                p_cut_start[1] = p_cut_start[1] + zw + 1
                continue

            # 从后往前
            for w in range(wt):
                # 必然有几乎全是 0 的行
                if self.np_almost_all_is0(tn[:, wt - 1 - w]):
                    break
                else:
                    same = False
                    fw = w
            else:
                # 没有几乎全 0 的行
                return False

            if fw is not None:
                p_cut_end[1] = p_cut_end[1] - fw - 1
                continue

            # 形状没有任何改变
            if same:
                break

        else:
            return False

        return True

    def detect_table_point(self, np_png, amin, amax, page_text):
        """
            只检查第 1 个表格

                    x000000000000000000000000000000000
            z       111111x000000000000111111111111111
                    1111111111111111111111111111111111  1 贯穿的空白 h
                    111111111111111111111111x000011111  x 干扰行
            a       1111∎000000000000∎00000000000∎1111
                    1111011111111111101111101111101111
                    1111011100100111101111010111101111
                    1111011111111111101111110111101111
            b       1111∎00000000000000000000000001111
                    1111011111001111101111111111101111
                    1111011100110011101110000111101111
                    1111011111111101101111111111101111
            c       1111∎00000000000000000000000001111
                    1111111111111111111111111111111111  1 贯穿的空白 h
                    x000000000000000000000000000000000

            关键点:

                [h]

            [w] a1  a2  a3
                b1
                c1

            表格线的长度 > 字体尺寸? * 5

        """
        h, w = np_png.shape
        hl = [(np_png[i, :]).all() for i in range(h)]

        # 默认存在 贯穿的空白 ，以此为标准切割高h（切割后选最大的区域） 🚸 应该取第 1 个足够大的区域吧
        h_points = self.calc_continue_point(hl)
        self.print("h_points is: %s of %s\n" % (h_points, (h, w)))

        for h_point in h_points:
            """
                计算区域内的字体的大小！，3个中文字符长度以上的可以视为符合条件，完美！

                表格最小 1 x 2：

                    1 x 中文字符 + (表格线+字符间隔) => 3中文字符 长度 （约记）

                    区域内没有字符 -> skip
            """
            content_text = [x for x in page_text if h_point[0] < (x[3] + x[1]) / 2 - amin < h_point[1]]

            # ⚠️ 是否需要改成直接从高度获取
            size_chr, size_de = self.calc_char_len(content_text)
            if not size_chr * size_de:
                continue

            if h_point[1] - h_point[0] < size_chr * 1.5:
                continue

            # h_point = sorted(h_points, key=lambda a: -(a[1] - a[0]))[0]
            self.print("[filter] h_point take: %s" % (h_point,))

            # 同理，在贯穿的空白内切割宽w
            # 注释前：可以处理同一行里的多个表格
            # 注释后：视为 1 个表格
            wl = [self.np_almost_all_is0(np_png[h_point[0]: h_point[1], i]) for i in range(w)]
            if True not in wl:
                continue
            w_point = [wl.index(True), len(wl) - wl[::-1].index(True)]
            w_point = (w_point[0], w_point[1], w_point[1] - w_point[0])

            p_cut_start = [h_point[0], w_point[0]]
            p_cut_end = [h_point[1], w_point[1]]

            self.print("doing fix zip cut points: ", p_cut_start, p_cut_end)
            self.save_process_image(np_png[p_cut_start[0]: p_cut_end[0], p_cut_start[1]: p_cut_end[1]], "tw.tn.png")

            # 压缩干扰行 逼近表格
            fixed = self.fix_zip_cut_points(np_png, p_cut_start=p_cut_start, p_cut_end=p_cut_end)
            if not fixed:
                continue

            self.save_process_image(np_png[p_cut_start[0]: p_cut_end[0], p_cut_start[1]: p_cut_end[1]], "tw.tn2.png")

            # 再次判断表格的大小，最小 1x2
            if (p_cut_end[0] - p_cut_start[0]) <= size_chr * 1.5:
                continue
            if (p_cut_end[1] - p_cut_start[1]) <= size_chr * 2.5:
                continue

            self.print("done fix zip cut points to: ", p_cut_start, p_cut_end)

            # 把表格的四条边给我抠出来
            np_table = np_png[p_cut_start[0]: p_cut_end[0], p_cut_start[1]: p_cut_end[1]]

            # if any([1 for x in content_text if '占基金资产净值比例' in x[-1]]):
            #     q.d()

            break

        else:
            return None

        self.save_process_image(np_table, "tw.t0.png")

        ht, wt = np_table.shape

        # 判断是否存在 1，存在则 True，以提取完全是 0 的表格线
        htl = [not self.np_almost_all_is0(np_table[i - 1:i + 2, :].all(axis=0)) for i in range(1, ht)]
        wtl = [not self.np_almost_all_is0(np_table[:, i - 1:i + 2].all(axis=1)) for i in range(1, wt)]

        htl.insert(0, htl[0])
        wtl.insert(0, wtl[0])

        wt_pointls = self.calc_continue_point(wtl)
        wt_points = list(map(lambda w: round((w[0] + w[1]) / 2), wt_pointls))

        ht_pointls = self.calc_continue_point(htl)
        ht_points = list(map(lambda h: round((h[0] + h[1]) / 2), ht_pointls))

        self.print()
        self.print("表格的行数 %s: 0~%s %s" % (len(ht_points) - 1, ht, ht_points))
        self.print(ht_pointls)

        self.print("表格的列数 %s: 0~%s %s" % (len(wt_points) - 1, wt, wt_points))
        self.print(wt_pointls)
        self.print()

        ht_points[0], wt_points[0] = (0, 0)     # 理所当然是 0
        # ht_points[-1], wt_points[-1] = (len(htl) - 1, len(wtl) - 1)     # 理所当然是 边长 （但是缩小一点范围也未尝不可）

        self.draw_a_table(np_table, ht_points, wt_points, "tw.t1.png")

        return (p_cut_start, p_cut_end, ht_points, wt_points)

    def draw_a_table(self, dn, ht_points, wt_points, name):

        # 筛选 w 和 h
        dc = np.zeros(dn.shape)
        h, w = dn.shape

        for hp in ht_points:
            dc[max(int(hp - 1), 0): min(int(hp + 1), h), :] = 1

        for wp in wt_points:
            dc[:, max(int(wp - 1), 0): min(int(wp + 1), w)] = 1

        self.save_process_image(dc, name)

    def cut_text(self, table_content, ht_points, wt_points):

        result = np.empty((len(ht_points) - 1, len(wt_points) - 1), dtype=np.object)
        result[:] = ""

        tloca = TextLoca(ht_points, wt_points)
        for line in table_content:
            h, w = tloca.do(line)
            result[h, w] = result[h, w] + line[4]

        return result

    def find_table(self, title):

        for page_no in range(self.page_count):

            page = self.pdf.loadPage(page_no)

            # 搜索标题，只匹配第 1 个结果
            search_rect = page.searchFor(title, hit_max=1)
            if not search_rect:
                continue

            self.print("Got result in page %s" % (page_no))

            # 取第 1 个结果的 结束，和页面最大值
            hmin = round((search_rect[0])[3])
            hmax = self.PAGE_MAX_SIZE

            # 获取 hmin ~ hmax 下面的所有文字
            page_texts = self.get_rect_text(page, [0, hmin, 9999, hmax])
            if not page_texts:
                self.print("No text below hmin %s" % (hmin))
                continue

            # 获取表格的关键点
            page_table_points = self.find_table_below(page, hmin, hmax, page_texts)
            if not page_table_points:
                self.print("Seems no table in this page %s." % page_no)
                continue

            # q.d()
            # 切割表格内的文字
            table_contents = self.find_content_in_table(page_table_points, page_texts)

            self.print("\ntable_contents:\n", table_contents)

            # 取当前页的结果
            page_next_texts = page_texts
            th_end_next = page_table_points[1][0]

            # q.d()

            while "判断跨页":

                # 判断 表格距离页面底部的高度
                table_end_space_rate = ((page.rect[3] - th_end_next) / page.rect[3])
                if table_end_space_rate > 0.125:
                    self.print("判断跨页：条件0失败，表格结束点 %s，页面高度 %s，距离页面底部高度 %s%% > 12.5%%" % (th_end_next, page.rect[3], round(table_end_space_rate * 100, 2)))
                    break
                else:
                    self.print("判断跨页：条件0成功，表格结束点 %s，页面高度 %s，距离页面底部高度 %s%% <= 12.5%%" % (th_end_next, page.rect[3], round(table_end_space_rate * 100, 2)))

                # 判断 页数 是否有效
                page_no = page_no + 1
                if self.page_count <= page_no:
                    self.print("判断跨页：已经达到最后一页")
                    break

                # 判断 表格下面的内容 不超过2行
                table_down_texts = [t for t in page_next_texts if t[1] > th_end_next]
                table_down_texts = sorted(table_down_texts, key=lambda x: x[1])

                if table_down_texts:

                    line_count = 1
                    for i in range(len(table_down_texts) - 1):
                        if 2 <= abs((table_down_texts[i][1] + table_down_texts[i][3]) / 2 - (table_down_texts[i + 1][1] + table_down_texts[i + 1][3]) / 2):
                            line_count = line_count + 1

                    if line_count > 2:
                        self.print("判断跨页：条件1失败，页脚内容行数 %s" % (line_count))
                        break

                    self.print("判断跨页：条件1成功，页脚内容行数 %s" % (line_count))

                # 开始处理下一页
                page_next = self.pdf.loadPage(page_no)

                # 获取 hmin ~ hmax 下面的所有文字
                page_next_texts = self.get_rect_text(page_next, [0, 0, 9999, self.PAGE_MAX_SIZE])
                if not page_next_texts:
                    self.print("判断跨页：条件1失败，页面 %s 无内容" % (page_no))
                    break

                # 获取表格的关键点
                page_next_table_points = self.find_table_below(page_next, 0, self.PAGE_MAX_SIZE, page_next_texts)
                if not page_next_table_points:
                    self.print("判断跨页：条件1失败，页面 %s 无表格" % (page_no))
                    break

                same_table = self.cmp_table_points(page_table_points, page_next_table_points)
                if not same_table:
                    self.print("判断跨页：条件2失败: 后一页的表格的格式不符合：\n%s\n%s" % (page_table_points, page_next_table_points))
                    break

                # 切割表格内的文字
                table_contents_next = self.find_content_in_table(page_next_table_points, page_next_texts)
                self.print("\ntable_contents_next:\n", table_contents_next)
                table_contents = np.concatenate([table_contents, table_contents_next])

                th_end_next = page_next_table_points[1][0]

            return table_contents
        else:
            self.print("Cannot find %s in %s" % (title, self.pdf_file))

        return None

    def cmp_table_points(self, page_table_points, page_next_table_points):
        """
            判断列的数量和宽度
        """
        if len(page_table_points) == len(page_next_table_points):

            # 判断列数
            tb_point_start, tb_point_end, ht_points, wt_points = page_table_points
            tb_point_start_next, tb_point_end_next, ht_points_next, wt_points_next = page_next_table_points
            if len(wt_points) == len(wt_points_next):

                # 判断每一列的列宽
                list_almost_same = all([abs(x - y) < 2 for x, y in zip(wt_points, wt_points_next)])
                if list_almost_same:
                    return True

        return False

    def find_table_below(self, page, hmin, hmax, page_texts):

        img_np = self.get_snapshot(page)
        page_h, page_w = img_np.shape

        # 像素化 与 页面尺寸 会有少许误差，但不应超过 1 个像素的误差
        if not (abs(page_h - page.rect[3]) < 1 and abs(page_w - page.rect[2]) < 1):
            raise Exception("Get snapshot fail size: %s -> %s" % ((page.rect[3], page.rect[2]), (page_h, page_w)))

        # 剪切出 标题下面的一切
        amin, amax = max(int(hmin + 1), 0), min(img_np.shape[0], 9999)
        self.save_process_image(img_np[amin:amax], "tw.1.png")

        # 计算表格的 关键点
        table_points = self.detect_table_point(img_np[amin:amax], amin, amax, page_texts)
        if not table_points:
            return None

        tb_point_start, tb_point_end, ht_points, wt_points = table_points

        # 修正计算 点的位置
        ht_points = [x + tb_point_start[0] + hmin for x in ht_points]
        wt_points = [x + tb_point_start[1] for x in wt_points]

        th_start = int(tb_point_start[0] + hmin)
        th_end = int(tb_point_end[0] + hmin)
        tw_start = tb_point_start[1]
        tw_end = tb_point_end[1]
        self.print("th_start: %s, th_end: %s, tw_start: %s, tw_end: %s" % (th_start, th_end, tw_start, tw_end))

        # 画出目标区域
        np_tmp = np.zeros(img_np.shape)
        np_tmp[th_start:th_end, tw_start:tw_end] = 1
        self.save_process_image(np_tmp, "tw.2.png")

        return ((th_start, tw_start), (th_end, tw_end), ht_points, wt_points)

    def find_content_in_table(self, page_table_points, page_texts):

        tb_point_start, tb_point_end, ht_points, wt_points = page_table_points

        # 只提取 表格内部 的内容
        table_content = list(filter(
            lambda x: (tb_point_start[0] < (x[3] + x[1]) / 2 < tb_point_end[0] and tb_point_start[1] < (x[0] + x[2]) / 2 < tb_point_end[1]),
            page_texts,
        ))

        self.print("cut text from table key points:", ht_points, wt_points)
        result = self.cut_text(table_content, ht_points, wt_points)

        return result


class TextLoca(object):

    def __init__(self, ht_points, wt_points):
        self.ht_points = ht_points
        self.wt_points = wt_points

    def loca_h(self, h):

        for i, th in enumerate(self.ht_points):
            if h < th:
                return i - 1

        return i

    def loca_w(self, w):

        for i, tw in enumerate(self.wt_points):
            if w < tw:
                return i - 1

        return i

    def do(self, line):

        return self.loca_h((line[1] + line[3]) / 2), self.loca_w((line[0] + line[2]) / 2)


if __name__ == "__main__":

    if 1:
        pdf_name = "../../tests/data/20200324164938兴全趋势投资混合型证券投资基金（LOF）2019年度报告.pdf"
        table_title = ("报告期末按行业分类的境内股票投资组合", "主要会计数据和财务指标", "基金份额净值增长率及其与同期业绩比较基准收益率的比较", "期末按公允价值占基金资产净值比例大小排序的前五名债券投资明细", "累计卖出金额超出期初基金资产净值", "期末按公允价值占基金资产净值比例大小排序的所有股票投资明细", "期末按债券品种分类的债券投资组合",)

    if 0:
        pdf_name = "../../tests/data/20190417181644xqqs.pdf"
        table_title = ("基金产品概况", "主要财务指标和基金净值表现", "本报告期基金份额净值增长率及其与同期业绩比较基准收益率的比较", "基金经理（或基金经理小组）简介", "基金经理（或基金经理小组）简介", "报告期末基金资产组合情况", "报告期末按行业分类的境内股票投资组合", "报告期末按公允价值占基金资产净值比例大小排序的前十名股票投资明细", "报告期末按债券品种分类的债券投资组合", "报告期末按公允价值占基金资产净值比例大小排序的前五名债券投资明细", "其他资产构成", "报告期末持有的处于转股期的可转换债券明细", )
        table_title = ("开放式基金份额变动", "基金管理人持有本基金份额变动情况", "报告期内单一投资者持有基金份额比例达到或超过 20%的情况")

    wk = Walker(pdf_name, debug=False)
    main_title = wk.find_main_title()
    print("main_title:", main_title)

    for title in table_title:
        table_contents = wk.find_table(title)
        print("\ntable_contents: %s\n" % (title))
        for line in table_contents:
            print(line)
        print()

