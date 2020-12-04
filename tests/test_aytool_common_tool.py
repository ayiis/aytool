#!/usr/bin/env python
# -*- coding: utf-8 -*-
import _conf_
import q
import re
import os
import zlib

import requests
from aytool.common.tool import ReLateSub
from aytool.common.tool import execute_command
from aytool.common.tool import PassException
from aytool.common.tool import try_decode_content

_conf_.valid_module_path(ReLateSub)

ungzip = lambda x: zlib.decompress(x, zlib.MAX_WBITS | 16)


def test_ReLateSub():

    trans_dict = {
        "the one": "3 xxxx",
        "TRIGSTR_001": "2 xxxx",    # NOT THIS
        "I am the one": "1 xxxx",
        "whoami": "4 xxxx",
    }

    RSTRING = r"(\\[trn]|[\t\n\r]|(\|[rn])?\-[a-z0-9]+|http[s]?\:\/\/[^\ \"\'\|]+|\<[a-z0-9]{4}(\:[a-z0-9]{4})?,[a-z0-9]+\>|TRIGSTR_[0-9]+|\%[a-z]\b|\|c[0-9a-f]{8}|[0-9\+\-\%]|\|n|\|r|[\~\!\@\#\$\^\&\*\(\)\_\=\`\[\]\\\{\}\|\;\:\"\,\.\/\<\>\?“”])"

    test_trans_line = "I am the one!TRIGSTR_001 http://www.baidu.com/ the one? whoami"

    result = ReLateSub.do(test_trans_line, RSTRING, trans_dict)
    print("result:", result)
    assert result == "1 xxxx?http://www.baidu.com/ TRIGSTR_001 3 xxxx! 4 xxxx"

    try:
        test_trans_line = "I am the one!TRIGSTR_001\x00 http://www.baidu.com/ the one? whoami"
        ReLateSub.do(test_trans_line, RSTRING, trans_dict)
    except Exception as e:
        assert str(e) == repr("目标字符串含有 \x00 终止符")
        print(e)
    else:
        raise Exception("Not supports to be here.")


def test_command():
    # res1 = execute_command("echo 123123 >/tmp/asfasfa.txt")
    # res1 = execute_command("cd /tmp/fff && git clone --filter=tree:0 --no-checkout https://github.com/ayiis/coding 8", "utf8")
    res1 = execute_command("cd /tmp/fff/8 && git log")
    print("res1:", res1)


def test_with():
    import time

    with PassException(desc="%s This will show if error occurs." % time.time()):
        pirnt(zzz)

    print("This will fire whatever happened in `with PassException()`.")

    with PassException() as pe:

        print("You Break here.")
        if True:
            raise pe.Break

        print("You will not see this")

    print("You are here")


def test_try_decode_content():

    target_url = "https://jd.com/"
    res = requests.get(target_url, headers={
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh-TW;q=0.7,zh;q=0.6",
        "Pragma": "no-cache",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36",
    }, stream=True)
    text = res.raw.read()
    text = ungzip(text)

    q.d()
    cc = text.decode("utf8")
    cc.encode("gb18030").decode("gb18030")

    text.decode("gb2312")
    text.decode("gbk")
    text.decode("gb18030")
    text.decode("big5")
    text.decode("big5hkscs")
    text = try_decode_content(text)


def main():
    # test_ReLateSub()
    # test_command()
    test_with()
    # test_try_decode_content()


if __name__ == "__main__":
    main()
