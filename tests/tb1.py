import q
import re
import cv2
import pandas as pd
import numpy as np
from operator import itemgetter
from sympy import symbols, solve

import table_content
"""
    算了，算累了，直接解析图片吧
"""

# table_text = table_content.content[0]
# table_text = table_content.content[1]
# table_text = table_content.content[2]   # bad, 麻烦的格式
# table_text = table_content.content[3]
table_text = table_content.content[4]


class Glb:
    """
        ⚠️ 前提 1: 中文字体的大小 >= 字体间空格 * 2
            不考虑例外情况：被 word 拉伸过的换行之类的句子

        ⚠️ 前提 2: 中文字体的大小 >= 数字、英文字体的大小

        ⚠️ 前提 3: 表格内的字体样式应是一样的
            不考虑刁钻的字体样式
    """
    PADDING_HEIGHT = 2  # 字符间隔
    SIZE_CHR = 10       # 中文字体大小
    SIZE_DE = 5         # 英文字体大小


def sym_calc(cond_list):
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
            raise Exception("Nothing to solve.")
    else:
        cond0 = cond_list[0]
        cond1 = cond_list[1]
        result = solve([
            x * cond0[0] + y * cond0[1] - cond0[2],
            x * cond1[0] + y * cond1[1] - cond1[2],
        ], [x, y])
        x, y = result.values()

    return float(x), float(y)


def calc_char_len(text):
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

    size_chr, size_de = sym_calc(cond_list)

    Glb.PADDING_HEIGHT = max(Glb.PADDING_HEIGHT, round(size_de / 2))
    print("size_chr: %s, size_de: %s, Glb.PADDING_HEIGHT: %s" % (round(size_chr, 2), round(size_de, 2), Glb.PADDING_HEIGHT))

    return size_chr, size_de


def save_png(dd, name):
    print("Save to:", name)
    _, imth = cv2.threshold(dd, 0, 255, cv2.THRESH_BINARY)
    cv2.imwrite(name, imth)


def calc_table():

    size_chr, size_de = calc_char_len(table_text)

    min_x0, min_x1, min_x2 = 0, 0, 0
    max_x0, max_x1, max_x2 = 0, 0, 0

    list_x0 = list(map(itemgetter(0), table_text))
    list_x1 = list(map(itemgetter(1), table_text))
    list_x2 = list(map(itemgetter(2), table_text))

    min_x0, max_x0 = min(list_x0), max(list_x0)
    min_x1, max_x1 = min(list_x1), max(list_x1)
    min_x2, max_x2 = min(list_x2), max(list_x2)

    print("高:", min_x1, max_x1)         # 高
    print("宽 开始:", min_x0, max_x0)    # 宽 开始
    print("宽 结束:", min_x2, max_x2)    # 宽 结束

    dn = np.zeros((max_x1 - min_x1 + 1 + Glb.PADDING_HEIGHT * 2, max_x2 - min_x0 + 1))

    def set_dn(dn, h, w1, w2, val=1):
        dn[
            max(0, h - min_x1 - Glb.PADDING_HEIGHT):min(h - min_x1 + Glb.PADDING_HEIGHT, max_x1 - Glb.PADDING_HEIGHT),
            max(0, w1 - min_x0 - Glb.PADDING_HEIGHT):min(w2 - min_x0 + Glb.PADDING_HEIGHT, max_x2 - Glb.PADDING_HEIGHT),
        ] = val

    for line in table_text:
        # 高, 宽开始, 宽结束
        set_dn(dn, line[1], line[0], line[2])

    # 画一个黑白的图片 可视化操作
    save_png(dn, "tmp.dn.png")

    def draw_the_line(dn):

        min_line_width = Glb.PADDING_HEIGHT

        # 判断 行和列 是否存在字符
        h, w = dn.shape
        hl = [(dn[i]).any() for i in range(h)]
        wl = [(dn[:, i]).any() for i in range(w)]

        if "计算 h 的切割":
            h_cut_width, h_cut = [], 0
            h_cut_pare = []
            # 如果连续的 False (不存在字符) 达到 line_width 则认为存在可能的 表格线
            for i in range(min_line_width, len(hl) - min_line_width):
                if not hl[i]:
                    h_cut += 1
                else:
                    if h_cut:
                        h_cut_pare.append((i - h_cut, i))
                        h_cut_width.append(h_cut)
                        h_cut = 0

            h_cut = max(2 * min_line_width + 1, min(h_cut_width))
            print("h_cut_width:", h_cut_width, h_cut)

        if "计算 w 的切割":
            w_cut_width, w_cut = [], 0
            w_cut_pare = []
            # 如果连续的 False (不存在字符) 达到 line_width 则认为存在可能的 表格线
            for i in range(min_line_width, len(wl) - min_line_width):
                if not wl[i]:
                    w_cut += 1
                else:
                    if w_cut:
                        w_cut_pare.append((i - w_cut, i))
                        w_cut_width.append(w_cut)
                        w_cut = 0

            q.d()
            w_cut = max(min_line_width + 1, min(w_cut_width))
            print("w_cut_width:", w_cut_width, w_cut)

        fin_w, fin_h = [], []

        # 筛选 w 和 h
        dc = np.zeros(dn.shape)
        for wp in w_cut_pare:
            if wp[1] - wp[0] < w_cut:
                continue

            minw = (wp[1] + wp[0]) / 2
            fin_w.append(minw)
            dc[:, int(minw - min_line_width / 2): int(minw + min_line_width / 2)] = 1

        for hp in h_cut_pare:
            if hp[1] - hp[0] < h_cut:
                continue

            minh = (hp[1] + hp[0]) / 2
            fin_h.append(minh)
            dc[int(minh - min_line_width / 2): int(minh + min_line_width / 2)] = 1

        save_png(dc, "tmp.dc.png")
        print("fin_h:", fin_h)
        print("fin_w:", fin_w)

        return fin_h, fin_w

    table_h, table_w = draw_the_line(dn)
    table_h = [x + min_x1 for x in table_h]
    table_w = [x + min_x0 for x in table_w]
    print("行:", len(table_h) + 1, table_h)
    print("列:", len(table_w) + 1, table_w)

    return table_h, table_w


def loca_wrap(table_h, table_w):

    def do(line):
        for i, h in enumerate(table_h):
            if h:
                pass

    return do


class Loca(object):

    def __init__(self, table_h, table_w):
        self.table_h = table_h
        self.table_w = table_w

    def loca_h(self, h):

        for i, th in enumerate(self.table_h):
            if h < th:
                return i - 1

        return i

    def loca_w(self, w):

        for i, tw in enumerate(self.table_w):
            if w < tw:
                return i - 1

        return i

    def do(self, line):

        return self.loca_h(line[1]), self.loca_w(line[0])


def cut_text(table_h, table_w):

    result = np.empty((len(table_h) + 1, len(table_w) + 1), dtype=np.object)
    result[:] = ""

    loca = Loca(table_h, table_w)

    line = table_text[0]

    for line in table_text:
        h, w = loca.do(line)
        result[h, w] = result[h, w] + line[4]

    return result


def cut_text2(table_h, table_w):

    result = np.empty((len(table_h) - 1, len(table_w) - 1), dtype=np.object)
    result[:] = ""

    loca = Loca(table_h, table_w)

    for line in table_text:

        try:
            h, w = loca.do(line)
            result[h, w] = result[h, w] + line[4]
        except Exception as e:
            print("e:", e)
            q.d()

    return result


def calc_continue_point(tf_list):

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


def draw_a_table(dn, ht_points, wt_points, name):

    # 筛选 w 和 h
    dc = np.zeros(dn.shape)
    h, w = dn.shape

    for hp in ht_points:
        dc[max(int(hp - 1), 0): min(int(hp + 1), h), :] = 1

    for wp in wt_points:
        dc[:, max(int(wp - 1), 0): min(int(wp + 1), w)] = 1

    save_png(dc, name)


# magic number
ALMOST_ALL = 0.968


def np_almost_all_is1(np_list):
    """
        全 1
    """
    return np_list.sum() / np_list.size > ALMOST_ALL


def np_almost_all_is0(np_list):
    """
        全 0
    """
    return np_list.sum() / np_list.size < 1 - ALMOST_ALL


def fix_zip_cut_points(dn, p_cut_start, p_cut_end):

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
            if np_almost_all_is0(tn[h]):
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
            if np_almost_all_is0(tn[ht - 1 - h]):
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
            if np_almost_all_is0(tn[:, w]):
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
            if np_almost_all_is0(tn[:, wt - 1 - w]):
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


def detect_table_point(np_png, amin, amax, page_text):
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
    h_points = calc_continue_point(hl)
    print("h_points is: %s of %s\n" % (h_points, (h, w)))

    for h_point in h_points:
        """
            计算区域内的字体的大小！，3个中文字符长度以上的可以视为符合条件，完美！

            表格最小 2 x 2：

                2 x 中文字符 + (表格线+字符间隔) => 3中文字符 长度 （约记）

                区域内没有字符 -> skip
        """
        content_text = [x for x in page_text if h_point[0] < x[1] - amin < h_point[1]]
        size_chr, size_de = calc_char_len(content_text)
        if not size_chr * size_de:
            continue

        if h_point[1] - h_point[0] < size_chr * 3:
            continue

        # h_point = sorted(h_points, key=lambda a: -(a[1] - a[0]))[0]
        print("[filter] h_point take: %s" % (h_point,))

        # 同理，在贯穿的空白内切割宽w
        # 注释前：可以处理同一行里的多个表格
        # 注释后：视为 1 个表格
        # wl = [np_almost_all_is1(np_png[h_point[0]: h_point[1], i]) for i in range(w)]
        # w_points = calc_continue_point(wl)
        # w_point = sorted(w_points, key=lambda a: -(a[1] - a[0]))[0]
        # print("w_point is: %s, take: %s" % (w_points, w_point))
        wl = [np_almost_all_is0(np_png[h_point[0]: h_point[1], i]) for i in range(w)]
        # w_points = calc_continue_point(wl)
        # w_point = (w_points[0][1], w_points[-1][1], w_points[-1][0] - w_points[0][1])
        w_point = [wl.index(True), len(wl) - wl[::-1].index(True)]
        w_point = (w_point[0], w_point[1], w_point[1] - w_point[0])

        p_cut_start = [h_point[0], w_point[0]]
        p_cut_end = [h_point[1], w_point[1]]

        print("doing fix zip cut points: ", p_cut_start, p_cut_end)

        # save_png(np_png[p_cut_start[0]: p_cut_end[0], p_cut_start[1]: p_cut_end[1]], "tmp.tn.png")
        # q.d()

        # 压缩干扰行 逼近表格
        fixed = fix_zip_cut_points(np_png, p_cut_start=p_cut_start, p_cut_end=p_cut_end)
        if not fixed:
            continue

        # 再次判断表格的大小，最小 3x3
        if (p_cut_end[1] - p_cut_start[1]) <= size_chr * 3:
            continue
        if (p_cut_end[0] - p_cut_start[0]) <= size_chr * 3:
            continue

        print("done fix zip cut points to: ", p_cut_start, p_cut_end)

        # 把表格的四条边给我抠出来
        np_table = np_png[p_cut_start[0]: p_cut_end[0], p_cut_start[1]: p_cut_end[1]]
        break

    else:
        raise Exception("Seems no table in this page.")

    save_png(np_table, "tmp.t0.png")

    ht, wt = np_table.shape

    # 判断是否存在 1，存在则 True，以提取完全是 0 的表格线
    htl = [not np_almost_all_is0(np_table[i - 1:i + 2, :].all(axis=0)) for i in range(1, ht)]
    wtl = [not np_almost_all_is0(np_table[:, i - 1:i + 2].all(axis=1)) for i in range(1, wt)]

    htl.insert(0, htl[0])
    wtl.insert(0, wtl[0])

    wt_pointls = calc_continue_point(wtl)
    wt_points = list(map(lambda w: round((w[0] + w[1]) / 2), wt_pointls))

    ht_pointls = calc_continue_point(htl)
    ht_points = list(map(lambda h: round((h[0] + h[1]) / 2), ht_pointls))

    print()
    print("表格的行数 %s: 0~%s %s" % (len(ht_points) - 1, ht, ht_points))
    print(ht_pointls)

    print("表格的列数 %s: 0~%s %s" % (len(wt_points) - 1, wt, wt_points))
    print(wt_pointls)
    print()

    ht_points[0], wt_points[0] = (0, 0)     # 理所当然是 0
    # ht_points[-1], wt_points[-1] = (len(htl) - 1, len(wtl) - 1)     # 理所当然是 边长 （但是缩小一点范围也未尝不可）

    draw_a_table(np_table, ht_points, wt_points, "tmp.t1.png")

    return p_cut_start, p_cut_end, ht_points, wt_points


def main():

    table_h, table_w = calc_table()
    result = cut_text(table_h, table_w)

    q.d()
    table_text

    print("\nresult:\n", result)

    return 


if __name__ == "__main__":
    main()
