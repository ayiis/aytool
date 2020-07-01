#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MONGODB 数据库连接 """

import tornado.gen
from motor.motor_tornado import MotorClient

DBS = {}


@tornado.gen.coroutine
def init(mongodb_config):
    authenticate_list = []

    for db_name in mongodb_config:
        db_conf = mongodb_config[db_name]
        DBS[db_name] = MotorClient(db_conf["HOST"], db_conf["PORT"])[db_conf["DATABASE_NAME"]]

        if db_conf.get("USERNAME") and db_conf.get("PASSWORD"):
            authenticate_list.append(DBS[db_name].authenticate(db_conf["USERNAME"], db_conf["PASSWORD"]))

        setattr(
            DBS[db_name],
            "get_next_sequence",
            lambda sequence_name, db_name=db_name: get_next_sequence(DBS[db_name], sequence_name)
        )

    yield authenticate_list
    yield [db.get_next_sequence("sequence_counters") for db in DBS.values()]


@tornado.gen.coroutine
def get_next_sequence(dbname, sequence_name):
    """
        input a string output a uniqlo sequence number for this string in this db
    """
    doc = yield dbname.sequence_counters.find_one_and_update(
        filter={"_id": sequence_name},
        update={"$inc": {"sequence_number": 1}},
        upsert=True
    )
    if doc is None:
        doc = {"sequence_number": 0}

    raise tornado.gen.Return(str(doc["sequence_number"]))
