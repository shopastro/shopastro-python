import requests
import packs.ins_login as login
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
    print('fetch_domain_url',url)
    result = requests.get(url,timeout=20)
    return result


def data_file_exist(domain_host, domain, data_type, biz_date):
    url = "{0}/local/data/ins/file/exists?domain={1}&dataType={2}&bizDate={3}".format(domain_host, domain, data_type,
                                                      biz_date)
    print('file_exist_url',url)
    result = requests.get(url,timeout=20)
    return result


def upload_s3_and_update(domain_host, domain, data_base, data_type, biz_date):
    url = "{0}/local/data/ins/s3/upload?domain={1}&&dataBase={2}&&dataType={3}&bizDate={4}".format(domain_host, domain,
                                                                                                   data_base,
                                                                                                   data_type,
                                                                                                    biz_date)
    print('upload_s3_url', url)
    result = requests.get(url)
    return result


def user_login(user_name, pass_word):
    # 循环3次,三次登录都失败,结束流程
    login_result = ''
    for count in range(1, 4):
        post_init = login.post(user_name, pass_word)
        post_init.login
        login_result = post_init.check_auth()
        print(login_result)
        if login_result == 'Logged in Successfully':
            return True
            break
        else:
            print('登录失败', count, '次', '5秒后重新登录...')
            time.sleep(5)
    else:
        print('3次登录失败,请检查账号是否异常/更换账号....')
        return False


def tori_data(login_status, hash_tag):
    # 判断是否登录成功
    if login_status is True:
        tag_result = tags.access_tag_page(hash_tag)
        if 'data' in tag_result:
            blog.access_blog_page(hash_tag)
        else:
            print('tag=', hash_tag, '抓取tag数据失败......')
    else:
        pass


if __name__ == '__main__':

    user_name = input('请输入账号:\n')
    pass_word = input('请输入密码:\n')

    if user_name is not None and pass_word is not None:
        print('user_name',user_name)
        print('pass_word',pass_word)
        while True:
            host_ip = get_host_ip()
            domain_host = 'http://' + host_ip + ':48888';
            print('domain_host',domain_host)
            biz_date = time.strftime("%Y-%m-%d", time.localtime())
            # 获取执行的tag
            print('正在获取可执行的tag....')
            domain_data = fetch_domain(domain_host, biz_date)
            print('获取到tag数据',domain_data)
            if domain_data.text is not None and domain_data.text != '':
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
                    login_status = user_login(user_name, pass_word)
                    if login_status:
                        tori_data(login_status, domain)
                    else:
                        break

                    upload_s3_and_update(domain_host, domain, data_base, data_type, biz_date)



            else:
                print("DomainParameterError Sleep20Seconds")
                time.sleep(20)
    else:
        print('账号密码为空,请重新执行脚本.....')
