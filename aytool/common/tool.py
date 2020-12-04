#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" 公共方法 """

import os
import re
import json
import datetime
import subprocess
from datetime import timedelta
import time
import decimal
import zlib
import hashlib
import traceback

from bson.objectid import ObjectId
from inspect import getframeinfo, stack


class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            if obj == datetime.datetime.min:
                return None
            else:
                return obj.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(obj, datetime.date):
            if obj == datetime.date.min:
                return None
            else:
                return obj.strftime("%Y-%m-%d")
        elif isinstance(obj, timedelta):
            return time.strftime("%H:%M:%S", time.localtime(obj.seconds + 60 * 60 * (24 - 8)))  # hacked
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        # elif isinstance(obj, enum.Enum):
        #     return obj.value
        elif isinstance(obj, Exception):
            return {
                "error": obj.__class__.__name__,
                "args": obj.args,
            }
        elif isinstance(obj, ObjectId):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)


def json_dumps(data, **args):
    return json.dumps(data, cls=MyEncoder, ensure_ascii=False, **args)


def json_loads(data):
    return json.loads(data)


def gzip_encode(string):
    gzip_compressobj = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)
    return gzip_compressobj.compress(string) + gzip_compressobj.flush()


def gzip_decode(g_data):
    return zlib.decompress(g_data, zlib.MAX_WBITS | 32)


def fixed_float(num, fixed=2):
    """
        * 统一修复浮点数的不精确缺陷
            * @test 35.855 73.315 1.005 859.385 0.045
            1.04999999999999994 == 1.05
            1.0049999999999998 == 1.005
            1.0499999999999997 == 1.0499999999999996 == 1.0499999999999995
        精确到亿 999999999
    """
    return round(float("%fe-%s" % (round(float("%fe+%s" % (num, fixed)), 0), fixed)), fixed)


def aprint(*args):
    """
        禁止在生产环境使用
        输出信息比 print 多了 文件行数
    """
    caller = getframeinfo(stack()[1][0])
    date_string = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    caller_string = "%s@%s:" % (caller.filename, caller.lineno)
    return print(date_string, caller_string, *args)


def get_datetime_string(strftime="%Y-%m-%d %H:%M:%S"):
    return time.strftime(strftime, time.localtime(time.time()))


def get_date_string():
    return get_datetime_string("%Y-%m-%d")


def get_the_date(date_type, strftime="%Y-%m-%d"):
    now = datetime.datetime.now()
    if date_type == "today":
        target_date = now
    elif date_type == "tomorrow":
        target_date = now + timedelta(days=1)
    elif date_type == "week_start":
        target_date = now - timedelta(days=now.weekday())
    elif date_type == "week_end":
        target_date = now + timedelta(days=6 - now.weekday())
    elif date_type == "month_start":
        target_date = datetime.datetime(now.year, now.month, 1)
    elif date_type == "month_end":
        target_date = datetime.datetime(now.year, now.month + 1, 1) - timedelta(days=1)
    elif date_type == "year_start":
        target_date = datetime.datetime(now.year, 1, 1)
    elif date_type == "year_end":
        target_date = datetime.datetime(now.year + 1, 1, 1) - timedelta(days=1)
    else:
        target_date = now + timedelta(days=int(date_type))

    return target_date.strftime(strftime)


def try_decode_content(content, encoding_list=["utf8", "gb2312", "gbk", "gb18030", "big5", "big5hkscs"]):
    """
        常用于京东：
            gbk => gb18030 ==> UnicodeDecodeError: 'gbk' codec can't decode byte 0x81 in position
    """
    if content is None or isinstance(content, str):
        return content

    for encoding in encoding_list:
        try:
            return content.decode(encoding)
        except Exception:
            pass

    return content


def get_md5(text):
    if not isinstance(text, bytes):
        text = text.encode("utf8")
    else:
        pass
    return hashlib.md5(text).digest().hex()


def convert_stamp_to_datetime(stamp, strftime="%Y-%m-%d %H:%M:%S"):
    return time.strftime(strftime, time.localtime(int(stamp)))


class ReLateSub:
    """
        常用于整句翻译，将不需要翻译的部分字符串分组提取出来，翻译完成后再填充回去
            1. 将句子里的 网址｜特殊符号｜固定名词｜数字 等提取出来，保存在列表，原来的位置使用 \x00 占位
            2. 翻译句子，完全匹配。先翻译长句再翻译短句
            3. 用列表保存的 网址｜特殊符号｜固定名词｜数字 等把占位的 \x00 替换回来
            4. 返回结果

        示范：
            result = ReLateSub.do(test_trans_line, RSTRING, trans_dict)
    """
    re_cache = []
    default_escape = "\x00"

    def do(line, rstring_keep, trans_dict):
        """
            * 默认：此方法不需要对翻译词典进行排序，适用于 词典覆盖全面 的情况
                - 对翻译词典进行排序的方法（适用于 词典覆盖不全面 的情况）已删除
            line: 目标句子
            rstring_keep: 网址｜特殊符号｜固定名词｜数字 等
            trans_dict: 翻译对应的词典
        """
        ReLateSub.re_cache.clear()

        # 检查是否有 default_escape
        if ReLateSub.default_escape in line:
            raise Exception(repr("目标字符串含有 %s 终止符" % ReLateSub.default_escape))

        # 提取网址｜特殊符号｜固定名词｜数字 等，保存到 ReLateSub.re_cache
        line = re.sub(rstring_keep, ReLateSub.re_escape, line)
        keys = [x.strip() for x in line.split(ReLateSub.default_escape) if x.strip()]
        keys = sorted(set(keys), key=lambda x: -len(x))
        # 排序，先翻译长句再翻译短句
        for raw in keys:
            trans = trans_dict.get(raw, raw)
            line = re.sub(re.escape(raw), trans, line, flags=re.I)

        # 将 ReLateSub.re_cache 替换回来
        result = re.sub("[%s]" % ReLateSub.default_escape, ReLateSub.re_unescape, line)

        # 检查是否有 default_escape
        if ReLateSub.re_cache:
            raise Exception(repr("翻译内容含有 %s 终止符" % ReLateSub.default_escape))

        return result

    def re_escape(match):
        ReLateSub.re_cache.append(match.group(0))
        return ReLateSub.default_escape

    def re_unescape(match):
        return ReLateSub.re_cache.pop()


def read_with_linesep(fr, linesep):
    """
        open 的 newline 参数默认只能是 [\n][\r][""]，此处自己实现了一个自定义换行符的方法
        返回一个迭代器。

        with open("./test.txt", "rb") as rf:
            for line in read_with_linesep(rf, b"\x02"):
                print("line:", line)
    """
    # 根据 linesep 的数据类型判断 char_join 的数据类型
    if isinstance(linesep, bytes):
        char_join = b""
    else:
        char_join = ""

    # 缓存读取的数据
    sentense = []
    while True:
        char = fr.read(1)
        # 文件结束，如果 sentense 有数据则返回
        if not char:
            if sentense:
                yield StopIteration(char_join.join(sentense))
            else:
                yield StopIteration()
            break
        # 读到 linesep
        elif char == linesep:
            yield char_join.join(sentense)
            sentense.clear()
        else:
            sentense.append(char)


def execute_command(command, encoding=None):
    """
        在 MacOS 下，两种方式未见区别
    """
    if not encoding:
        return os.popen(command).read()
    else:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()
        return (out or err).decode(encoding)


class PassException(object):
    """
        No exception will be raised under this statement:
        Ignore: KeyboardInterrupt / Error

        e.g.

            with PassException("This will show if error occurs.") as pe:
                ffff(zzz)

            print("This will fire whatever happened in `with PassException()`.")

            >>> 🚸 PassException NameError: name 'ffff' is not defined

        Break:
            https://stackoverflow.com/questions/11195140/break-or-exit-out-of-with-statement

            with PassException() as pe:
                if True:
                    print("You Break here.")
                    raise pe.Break

                print("You will not see this")

            >>> You Break here.
            >>>
    """
    class Break(Exception):
        """Break out of the with statement"""
        pass

    def __init__(self, desc="No desc"):
        self.desc = desc

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):

        if exc_type == self.Break:
            return True

        if exc_traceback:
            print("%s %s: %s" % ("🚸PassException", exc_type.__name__, ",".join(exc_value.args)))
            traceback.print_tb(exc_traceback)
            print(self.desc)
            print()

            # Magic trick: ignore all exceptions by returning `True`
            return True
