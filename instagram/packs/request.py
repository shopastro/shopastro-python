import requests
import sys

sys.path.append('../')
from ip.ip_pond import choice_usable_proxy


init_proxy = choice_usable_proxy()
proxies = {
    "http": "http://" + init_proxy,
    "https": "https://"+ init_proxy
}


class RequestConfig:
    @staticmethod
    def req_session():
        requests.packages.urllib3.disable_warnings()
        requests.adapters.DEFAULT_RETRIES = 5  # 增加重连次数
        request_session = requests.session()
        request_session.keep_alive = False  # 关闭多余连接
        request_session.verify = False
        request_session.proxies = proxies
        return request_session


def cutover_proxy():
    global proxies
    while True:
        proxy = choice_usable_proxy()
        if proxy == '':
            print('暂无可用资源....')
            break
        proxies["http"] = "http://" + proxy
        print("获取到可用的ip", proxy)
        print("当前可用ip:", proxies)
        break
