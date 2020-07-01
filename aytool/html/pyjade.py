#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    Build the .jade file into html recursively.
    https://github.com/pugjs/pug
    https://github.com/syrusakbary/pyjade
"""
import os
from pyjade.utils import process
from pathlib import Path
from pyjade.ext.html import Compiler


def convert_file(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as rf:
        output = process(rf.read(), compiler=Compiler, staticAttrs=True, extension=None)
        with open(output_file, "w", encoding="utf-8") as wf:
            wf.write(output)


def build(source_path="templates_jade", target_path="templates", recursive=True):

    if not Path(target_path).exists():
        os.makedirs(target_path)
    elif not Path(target_path).is_dir():
        raise Exception("%s is not a dir!" % target_path)

    for path in Path(source_path).glob("*"):
        path_string = "%s" % path

        if recursive and path.is_dir():
            build("%s/%s" % (source_path, path.name), "%s/%s" % (target_path, path.name))

        elif path.is_file() and path_string[-5:] == ".jade" and len(path_string) > 5:
            convert_file("%s/%s" % (source_path, path.name), "%s/%s" % (target_path, path.name[:-5]))
