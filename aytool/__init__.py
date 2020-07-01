#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# __author__ = "ayiis"
# create on 2019/01/01
import time

MAIN_VERSION = 0
__version__ = version = "%s.%s" % (
    MAIN_VERSION,
    time.strftime("%y%m.%d%H%M", time.localtime(time.time()))
)

from aytool import (
    common,
    spider,
)

