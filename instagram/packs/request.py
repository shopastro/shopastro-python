from __init__ import *
import random
import requests
import sys
sys.path.append("..")
from ip_pond import test_ip,proxy_list




proxies = {
    "http": "http://" + random.choice(proxy_list())
}

class RequestConfig:
    @staticmethod
    def req_session():
        requests.packages.urllib3.disable_warnings()
        requests.adapters.DEFAULT_RETRIES = 5  # 增加重连次数
        request_session = requests.session()
        request_session.keep_alive = False  # 关闭多余连接
        request_session.proxies = proxies
        request_session.verify = False
        return request_session


def cutover_proxy():
    global proxies
    while True:
        proxy = random.choice(proxy_list())
        flag = test_ip(proxy)
        if flag:
            proxies["http"] = "http://"+proxy
            print("获取到可用的ip",proxy)
            print("当前可用ip:",proxies)
            break

