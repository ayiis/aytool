#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys
import inspect

sys.path.insert(0, os.path.abspath(".."))


def valid_module_path(module):
    module_path = inspect.getabsfile(module)
    if not re.match(sys.path[0], module_path):
        raise Exception("Import %s from %s NOT IN %s" % (module, module_path, sys.path[0]))
