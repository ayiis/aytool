#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# __author__ = "ayiis"
# create on 2019/03/07
"""
    表格化输出

    ┌───┬─────┬───────┐
    │ 1+│  11 │  1111 │
    ├───┴─────┼───┬───┤
    │    1111 │ 11│ 0 │
    ├───┬─────┴───┼───┤
    │ a │       a │   │
    └───┴─────────┴───┘

    支持无限细分
        1. 获取全部行的 切分点
        2. 用 切分点 填充每一行

        [0,0,0,0,0,0,1,0,0,0]
        [0,0,0,1,0,0,0,0,0,0]
        [0,0,0,0,0,0,1,0,0,0]

        => [0,0,0,1,0,0,0,1,0,0,0]

    中文限于字体问题，不一定能准确显示

"""


class PrettyTable(object):
    """
        表格头：根据第一行决定
                -- 内容 --
            行1：
                -- 内容 --
            行2
                -- 内容 --
        表格尾：根据最后一行决定
    """
    def __init__(self, arg=None):
        super(PrettyTable, self).__init__()
        self.arg = arg
        self.size_lists = []
        self.text_lists = []
        self.padding = 2
        self.padding
        self.tb = {
            "top_left": "┌",
            "top_right": "┐",
            "bottom_left": "└",
            "bottom_right": "┘",
            "row_sep": "│",
            "line_sep": "─",
            "line_left": "├",
            "line_right": "┤",
            "line_to_bottom": "┬",
            "line_cross": "┼",
            "line_to_top": "┴",
        }
        self.tb_mid_pair = {
            0: self.tb["line_sep"],
            1: self.tb["line_to_top"],
            2: self.tb["line_to_bottom"],
            3: self.tb["line_cross"],
        }
        self.tb_top_pair = {
            0: self.tb["line_sep"],
            1: self.tb["line_to_bottom"],
            2: self.tb["line_to_bottom"],
            3: self.tb["line_to_bottom"],
        }
        self.tb_bottom_pair = {
            0: self.tb["line_sep"],
            1: self.tb["line_to_top"],
            2: self.tb["line_to_top"],
            3: self.tb["line_to_top"],
        }

    def add_line(self, size_list, text_list):

        if len(size_list) != len(text_list):
            raise Exception("item count must be the same: %s and %s" % (size_list, text_list))

        if len(self.size_lists) > 0:
            if sum(size_list) != sum(self.size_lists[0]):
                raise Exception("Total size must be %s: now is %s of %s" % (sum(self.size_lists[0]), sum(size_list), size_list))

        self.size_lists.append(size_list)
        self.text_lists.append([str(t) for t in text_list])

    def get_text_len(self, text):
        sum_len = 0
        for c in text:
            if ord(c) < 128:
                sum_len = sum_len + 1
            else:
                sum_len = sum_len + 2

        return sum_len

    def get_text_until_len(self, text, size):

        sum_len = 0
        for i, c in enumerate(text):
            if ord(c) < 128:
                sum_len = sum_len + 1
            else:
                sum_len = sum_len + 2

            if size == sum_len:
                return text[:i + 1]
            elif size < sum_len:
                return text[:i] + " "

        return text

    def cut_word(self, text, size):

        text_size = self.get_text_len(text)
        if text_size <= size:
            return " %s%s " % (" " * (size - text_size), text)
        if text_size == size + 1:
            return " %s" % (text)

        return " %s+" % (self.get_text_until_len(text, size))

    def handle_size_list(self):

        concat = lambda clist, sep: (
            lambda dlist: dlist[0] + [y for x in dlist[1:] for y in [sep] + x]
        )(
            [[1] * (x + self.padding) for x in clist]
        )

        size_pad = [concat(x, 0) for x in self.size_lists]

        i = -1
        while i < max(map(len, size_pad)) - 1:

            i = i + 1
            if all((x[i] for x in size_pad)):
                continue

            for symbol in size_pad:
                if not symbol[i]:
                    continue
                else:
                    symbol[i:i] = [1] * (1 + self.padding)

        return size_pad

    def handle_text_list(self, size_pad):

        size_lists = [[len(z) - self.padding for z in "".join([str(y) for y in x]).split("0")] for x in size_pad]
        text_lists = self.text_lists

        text_pad = []
        for i, text_list in enumerate(text_lists):
            size_list = size_lists[i]
            pair_list = [self.cut_word(text, size) for size, text in zip(size_list, text_list)]
            text_pad.append(pair_list)

        return text_pad

    def get_table(self):

        if not self.size_lists:
            return ""

        size_pad = self.handle_size_list()
        text_pad = self.handle_text_list(size_pad)

        res_table = []

        for i in range(0, len(size_pad)):

            if i == 0:
                line = self.tb["top_left"] + "".join([self.tb_top_pair[not x] for x in size_pad[i]]) + self.tb["top_right"]
            else:
                line = self.tb["line_left"] + "".join([self.tb_mid_pair[(not x) + 2 * (not y)] for x, y in zip(size_pad[i - 1], size_pad[i])]) + self.tb["line_right"]

            res_table.append(line)
            text = self.tb["row_sep"] + self.tb["row_sep"].join(text_pad[i]) + self.tb["row_sep"]
            res_table.append(text)

            if i == len(size_pad) - 1:
                line = self.tb["bottom_left"] + "".join([self.tb_bottom_pair[not x] for x in size_pad[i]]) + self.tb["bottom_right"]
                res_table.append(line)

        return res_table

    def print_table(self):
        res_table = self.get_table()
        print("\n".join(res_table))


if __name__ == "__main__":

    pt = PrettyTable()
    pt.add_line((4, 4, 8, 4, 2), [1111, 1111, 11111111, 111111, 111])
    pt.add_line((8, 4, 10), ["2222", "2", "22"])
    pt.add_line((8, 2, 2, 2, 2, 2, 4), [2222, "1你", "你1", "1你好", "你好", "你1好", 2])
    pt.print_table()

