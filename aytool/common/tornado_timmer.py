#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tornado.ioloop
import tornado.gen
import datetime
import time


def sleep(timeout_seconds):
    return tornado.gen.sleep(timeout_seconds)


def set_timeout(timeout_seconds, outter_func):
    return tornado.ioloop.IOLoop.current().add_timeout(tornado.ioloop.IOLoop.current().time() + timeout_seconds, outter_func)


def set_interval(timeout_seconds, outter_func):
    interval_job = tornado.ioloop.PeriodicCallback(outter_func, timeout_seconds * 1000)
    interval_job.start()
    return interval_job


# run function at the same time of day
def set_clock(clock, outter_func):
    next_ts = datetime.datetime.strptime(
        str(datetime.date.today()) + " " + clock, "%Y-%m-%d %H:%M:%S")
    next_ts = time.mktime(next_ts.timetuple())
    next_ts = next_ts - tornado.ioloop.IOLoop.current().time()
    if next_ts < 0:
        next_ts = 60 * 60 * 24 + next_ts

    def _set_clock_callback():
        outter_func()
        return set_interval(60 * 60 * 24, outter_func)
    return set_timeout(next_ts, _set_clock_callback)


def remove_timeout(timeout):
    tornado.ioloop.IOLoop.current().remove_timeout(timeout)


def remove_interval(interval_job):
    interval_job.stop()
