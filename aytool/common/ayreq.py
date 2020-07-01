#! /usr/bin/env python
# -*- coding: utf-8 -*-
import threading
import queue
import time
import logging
import traceback
import http.client
import q
import re
"""
    其实效果和 request 的 connection keep alive 功能类似
"""


class HttpPreload(threading.Thread):
    """
        preload DNS query and http handshake to speedup http request
        传输时间减少 20~30%
        适用场景：
            低频率/高实时 的对同一个网站的请求
            例如对外部第三方接口的调用请求
        实现原理：
            预先建立连接，缓存
            连接被使用后||缓存超过一定时间后 重新创建连接并缓存
    """
    def __init__(self, conf):
        super(HttpPreload, self).__init__()
        self.target_site = conf["target_site"]
        self.in_queue = conf["in_queue"]
        self.out_queue = conf["out_queue"]
        self.connection = conf["https"] and http.client.HTTPSConnection or http.client.HTTPConnection
        self.cache_conn = None
        self.cache_ts = None
        self.stop = False

    def get_queue(self, in_queue):
        """
            从queue读取请求信息
        """
        try:
            return in_queue.get(block=True, timeout=0.5)
        except queue.Empty:
            return None

    def run(self):
        """
            线程的主要方法：
                - 缓存连接
                - 如果缓存的连接过期，则重新建立连接
                - 从in_queue读取请求信息
                - 读取到请求信息则使用 缓存的连接完成整个请求
        """
        self.cache_ts = time.time()
        while not self.stop:
            try:
                if self.cache_conn is None or time.time() - self.cache_ts >= 9.0:
                    self.cache_url()

                req_data = self.get_queue(self.in_queue)
                if req_data is not None:
                    result = self.request(req_data)
                    self.out_queue.put(result)

            except Exception:
                print(traceback.format_exc())
            finally:
                self.close_conn()

    def cache_url(self):
        """
            缓存连接状态，如果connect不成功，重试2次
        """
        self.cache_ts = time.time()
        if self.cache_conn is not None:
            self.close_conn()

        for _ in range(3):
            try:
                self.cache_conn = self.connection(self.target_site, timeout=5)
                self.cache_conn.connect()
                break
            except Exception:
                print("cache_url error:", traceback.format_exc())
                self.close_conn()
        else:
            print("[error] cached failed.")
            time.sleep(2)

    def close_conn(self):
        """
            关闭连接
        """
        try:
            if self.cache_conn is None:
                return
            self.cache_conn.close()
        except Exception:
            print("cache_conn close error:", traceback.format_exc())
        finally:
            self.cache_conn = None

    def request(self, req_data):
        """
            请求目标并返回响应结果
        """
        if self.cache_conn is None:
            self.cache_url()
        try:
            self.cache_conn.request(
                req_data["method"],
                req_data["url"],
                req_data["body"],
                req_data["headers"]
            )
            return self.cache_conn.getresponse().read()
        except Exception:
            print("request error:", traceback.format_exc())
            return None
        finally:
            self.close_conn()


from urllib.parse import urlparse


class AyReq(object):

    __connection_cache__ = {}

    def construct(self, method, url, headers, body):
        urlp = urlparse(url)
        https = urlp[0] == "https"
        host = urlp[1]
        key = (urlp[0], urlp[1])
        if key not in AyReq.__connection_cache__:
            conf = {
                "in_queue": queue.Queue(),
                "out_queue": queue.Queue(),
                "target_site": host,
                "https": https,
            }
            http_preload = HttpPreload(conf)
            http_preload.setDaemon(True)
            http_preload.start()

            conf["http_preload"] = http_preload
            AyReq.__connection_cache__[key] = conf
        else:
            conf = AyReq.__connection_cache__[key]

        req_data = {
            "method": "GET",
            "url": "%s?%s" % (urlp.path, urlp.query),
            "body": body,
            "headers": headers,
        }
        conf["in_queue"].put(req_data)

        return conf["out_queue"].get()

    def get(self, url, headers={}, body=None):
        return self.construct("GET", url, headers, body)

    def post(self, url, headers={}, body=None):
        return self.construct("POST", url, headers, body)


if __name__ == "__main__":
    ar = AyReq()
    res = ar.get("https://www.baidu.com:443/")
    print("res:", len(res))
    time.sleep(1)
    res = ar.get("https://www.baidu.com:443/")
    print("res:", len(res))
    # main()
