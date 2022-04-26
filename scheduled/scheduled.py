import schedule
import time
import os
import pathlib
import sys

sys.path.append('../')
from ip.ip_pond import get_kuaidaili_open_ip, test_ip


def job():
    ip_lst = []
    print('查询是否已经生成ip池文件...')
    path = pathlib.Path('../usable_ips.txt')
    flag = path.exists()
    if flag:
        with open('../usable_ips.txt', 'r') as ip_file:
            ip_lst = eval(ip_file.read())

        print('文件已存在,测试是否有可用的ip....')
        if len(ip_lst) > 0:
            usable_ip_lst = []
            for ip in ip_lst:
                # 校验ip是否可用
                ip_flag = test_ip(ip)
                if ip_flag:
                    usable_ip_lst.append(ip)
            else:
                # 循环结束,将可用的ip覆盖写回文本中
                with open("../usable_ips.txt", 'w') as ip_file:
                   ip_file.write(str(usable_ip_lst))

        else:
            # 文件中不存在ip信息,删除文件
            os.remove('../usable_ips.txt')
            print("文件中获取到的ip可用数为0,重新爬取公开ip.....")
            # 爬取快代理网站公开ip
            get_kuaidaili_open_ip()

    else:
        print('文件不存在...开始爬取公开网站Ip...')
        # 爬取快代理网站公开ip
        get_kuaidaili_open_ip()




if __name__ == '__main__':
    schedule.every(5).minutes.do(job)

    while True:
        print('运行所有可以执行的任务.....')
        schedule.run_pending()  # 运行所有可以运行的任务
        time.sleep(30)