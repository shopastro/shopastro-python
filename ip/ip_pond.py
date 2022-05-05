import pathlib
import random
import traceback
import requests  # 导入模块
from lxml import etree
from fake_useragent import UserAgent
import json


# 简单的反爬，设置一个请求头来伪装成浏览器
def request_header():
    headers = {
        # 'User-Agent': UserAgent().random #常见浏览器的请求头伪装（如：火狐,谷歌）
        'User-Agent': UserAgent().Chrome  # 谷歌浏览器
    }
    return headers


'''
创建两个列表用来存放代理ip
'''


# 发送请求，获得响应
def get_kuaidaili_open_ip():
    all_ip_list = []  # 用于存放从网站上抓取到的ip
    usable_ip_list = []  # 用于存放通过检测ip后是否可以使用
    # 爬取7页，可自行修改
    for i in range(1, 11):
        print(f'正在抓取第{i}页……')
        response = requests.get(url=f'https://www.kuaidaili.com/ops/proxylist/{i}/', headers=request_header())
        text = response.text.encode('utf-8')
        # print(text.decode('gbk'))
        # 使用xpath解析，提取出数据ip，端口
        html = etree.HTML(text)
        tr_list = html.xpath('/html/body/div/div[4]/div[8]/div/div/table/tbody/tr')

        for td in tr_list:
            if len(td.xpath('./td[1]/text()')) > 0:
                ip_ = td.xpath('./td[1]/text()')[0]  # ip
                port_ = td.xpath('./td[2]/text()')[0]  # 端口
                proxy = ip_ + ':' + port_  # 115.218.5.5:9000
                all_ip_list.append(proxy)
                # 开始检测获取到的ip是否可以使用
                flag = test_ip(proxy)
                if flag:
                    usable_ip_list.append(proxy)

            else:
                print('td len 0')

    print('抓取完成！')
    print(f'抓取到的ip个数为：{len(all_ip_list)}')
    print(f'可以使用的ip个数为：{len(usable_ip_list)}')
    print('分别有：\n', usable_ip_list)

    if len(usable_ip_list) > 0:
        with open('../usable_ips.txt', 'a') as ip_file:
            ip_file.write(str(usable_ip_list))


# 检测ip是否可以使用
def test_ip(proxy):
    # 构建代理ip
    proxies = {
        "http": "http://" + proxy,
        # "https": "https://" + proxy
        # "http": proxy,
        # "https": proxy,
    }
    try:
        response = requests.get(url='https://www.instagram.com/', headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux armv8l; rv:78.0) Gecko/20100101 Firefox/78.0"}, proxies=proxies,
                                timeout=10, verify=False)  # 设置timeout，使响应等待1s
        response.close()

        if response.status_code == 200:
            print(proxy, '\033[31m可用\033[0m')
            return True
        else:
            print('response', response.status_code)
            print(proxy, '不可用')
            return False

    except Exception as e:
        print(e)
        print(proxy, '请求异常')


# def choice_usable_proxy():
#     global ip_lst
#     usable_ip = ''
#     try:
#         path = pathlib.Path('../usable_ips.txt')
#         flag = path.exists()
#         if flag:
#             with open('../usable_ips.txt', 'r') as ip_file:
#                 ip_lst = eval(ip_file.read())
#
#             if len(ip_lst) > 0:
#                 for _ in ip_lst:
#                     ip = random.choice(ip_lst)
#                     flag = test_ip(ip)
#                     if flag:
#                         usable_ip = ip
#                         break
#
#         return usable_ip
#
#     except Exception:
#         print('file read Exception', traceback.print_exc())
#

ip_lst = []


def choice_usable_proxy():
    global ip_lst
    usable_ip = ''
    if not ip_lst:

        response = requests.get(
            url="http://api.proxy.ipidea.io/getProxyIp?num=100&return_type=json&lb=1&sb=0&flow=1&regions=us&protocol"
                "=http")
        json_data = json.loads(response.text)
        if json_data["success"]:
            list_data = json_data["data"]
            for ip_data in list_data:
                ip = ip_data["ip"]
                port = ip_data["port"]
                usable_ip = ip + ":" + port
                ip_lst.append(usable_ip)
        else:
            print("json_data",json_data)

    usable_ip = random.choice(ip_lst)
    flag = test_ip(usable_ip)
    if flag:
        print("ip_list",ip_lst)
        print("usable_ip",usable_ip)
        return usable_ip
    else:
        ip_lst.remove(usable_ip)


if __name__ == '__main__':
    # ip = input('输入要测试的ip: ')
    # test_ip(ip)
    choice_usable_proxy()
