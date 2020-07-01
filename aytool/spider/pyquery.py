from lxml import etree
from pyquery import PyQuery
"""
    BUG:
        1. dont use find like: PyQuery("div").find(".sub:eq(1)")
            - PyQuery("div")(":eq(1)")
        2. dont use > at first like: PyQuery("div")(">.sub")
            - PyQuery("div")(":eq(0)>.sub")

    I guess this cannot be fixed: https://github.com/gawel/pyquery/issues/139

    So ah, maybe I will goto use xpath with cssselector directly.
"""


def parse_content_to_dom(content):
    parser = etree.HTMLParser(encoding="utf-8")
    return PyQuery(etree.fromstring(content, parser=parser))


def iter_eles(elements):
    for i in range(len(elements)):
        yield i, elements.eq(i)
