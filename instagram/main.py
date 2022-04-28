import requests
from packs.ins_login import login_and_check
import packs.ins_tags_data as tags
import packs.ins_blog_data as blog
import socket
import time


def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
        return ip


def fetch_domain(domain_host, biz_date):
    url = "{0}/local/data/ins/domain/fetch?bizDate={1}".format(domain_host, biz_date)
    print('fetch_domain_url', url)
    result = requests.get(url, timeout=20)
    return result


def data_file_exist(domain_host, domain, data_type, biz_date):
    url = "{0}/local/data/ins/file/exists?domain={1}&dataType={2}&bizDate={3}".format(domain_host, domain, data_type,
                                                                                      biz_date)
    print('file_exist_url', url)
    result = requests.get(url, timeout=20)
    return result


def upload_s3_and_update(domain_host, domain, data_base, data_type, biz_date):
    url = "{0}/local/data/ins/s3/upload?domain={1}&&dataBase={2}&&dataType={3}&bizDate={4}".format(domain_host, domain,
                                                                                                   data_base,
                                                                                                   data_type,
                                                                                                   biz_date)
    print('upload_s3_url', url)
    result = requests.get(url)
    return result


def tori_data(hash_tag):
    print('开始爬取hashTag数据...')
    tag_result = tags.access_tag_page(hash_tag)
    if 'data' in tag_result:
        print('开始爬取博主数据...')
        blog.access_blog_page(hash_tag)
    else:
        print('tag=', hash_tag, '抓取tag数据失败......')


if __name__ == '__main__':

        while True:
            host_ip = get_host_ip()
            domain_host = 'http://' + host_ip + ':48888';
            print('domain_host', domain_host)
            biz_date = time.strftime("%Y-%m-%d", time.localtime())
            # 获取执行的tag
            print('正在获取可执行的tag....')
            domain_data = fetch_domain(domain_host, biz_date)
            print('获取到tag数据', domain_data)
            if domain_data.text != 'null' and domain_data.text != '':
                domain_lst = list(domain_data.text.split(','))
                shell = domain_lst[0]
                domain = domain_lst[1]
                data_base = domain_lst[2]
                data_type = domain_lst[3]
                print('StartFetch', 'domain=', domain, 'data_type=', data_type)

                # 查询数据文件是否存在
                result = data_file_exist(domain_host, domain, data_type, biz_date)
                if result.text != 'false':
                    print("LocalFile [%s]Exists Then UploadToS3\n", result.text)
                    upload_s3_and_update(domain_host, domain, data_base, data_type, biz_date)
                else:
                    login_and_check()
                    tori_data(domain)

                    upload_s3_and_update(domain_host, domain, data_base, data_type, biz_date)



            else:
                print("DomainParameterError Sleep20Seconds")
                time.sleep(20)
