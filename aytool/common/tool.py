#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" 公共方法 """

import re
import json
import datetime
from datetime import timedelta
import time
import decimal
import zlib
import hashlib

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
        elif isinstance(obj, datetime.timedelta):
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
    return datetime.datetime.now().strftime(strftime)


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


class RELaterSub(object):
    """
        常用于整句翻译，将不需要翻译的部分字符串分组提取出来，翻译完成后再填充回去
        示范：
        with RELaterSub(RSTRING, test_line) as rs:
            rs.line = re.sub(re.escape(key), ****, rs.line, flags=re.I)
            test_line = rs.finish()
    """
    default_escape = "\x00"
    default_unescape = r"[\0]"

    def __init__(self, rstring_keep, line):
        self.re_cache = []
        self.line = re.sub(rstring_keep, self.re_escape, line)

    def re_escape(self, match):
        self.re_cache.append(match.group(0))
        return self.default_escape

    def re_unescape(self, match):
        try:
            return self.re_cache.pop()
        except Exception:
            raise Exception("字符串里面不能含有 \\0 终止符")

    def finish(self):
        return re.sub(self.default_unescape, self.re_unescape, self.line)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass
