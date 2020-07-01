#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# - author: ayiis@2018/07/12
"""
    MONGODB 数据库连接初始化
    http://api.mongodb.com/python/current/tutorial.html
"""

from pymongo import MongoClient

DBS = {}


def init_connection(mongodb_config):

    for db_name in mongodb_config:

        db_conf = mongodb_config[db_name]
        DBS[db_name] = MongoClient("%s:%s" % (db_conf["HOST"], db_conf["PORT"]))[db_conf["DATABASE_NAME"]]

        if db_conf.get("USERNAME") and db_conf.get("PASSWORD"):
            DBS[db_name].authenticate(db_conf["USERNAME"], db_conf["PASSWORD"])

        setattr(
            DBS[db_name],
            "get_next_sequence",
            lambda sequence_name, db_name=db_name: get_next_sequence(DBS[db_name], sequence_name)
        )

    [db.get_next_sequence("sequence_counters") for db in DBS.values()]


def get_next_sequence(dbname, sequence_name):
    """
        input a string output a uniqlo sequence number for this string in this db
    """
    doc = dbname.sequence_counters.find_one_and_update(
        filter={"_id": sequence_name},
        update={"$inc": {"sequence_number": 1}},
        upsert=True
    )
    if doc is None:
        doc = {"sequence_number": 0}

    return str(doc["sequence_number"])
