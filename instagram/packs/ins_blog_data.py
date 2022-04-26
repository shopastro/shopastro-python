import time
import traceback
import re
import os
import requests
from .request import RequestConfig as reqc,cutover_proxy
from fake_useragent import UserAgent

def request_header():
    headers = {
        'User-Agent': UserAgent().Chrome,  # 谷歌浏览器
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9'
        # 'Origin': 'https://www.instagram.com',
        # 'Referer': 'https://www.instagram.com/',
    }
    return headers


def get_cookie():
    with open('../cookies.txt', 'r') as file:
        return file.read()


class Request:

    def __init__(self, headers, cookies):
        self.headers = headers
        self.cookies = cookies

    def get_blog_page(self, url):
        return reqc.req_session().get(f'{url}/', headers=self.headers, cookies=self.cookies, verify=False, timeout=30)


def access_blog_page(tag):
    blog_url_lst = []
    user_blog_list = []
    pic_url_hd_list = []
    data_time = time.strftime("%Y-%m-%d", time.localtime())
    try:
        write_path = os.path.expandvars('$HOME') + '/tmp'
        with open('{0}/{1}-blog-url-{2}.txt'.format(write_path,tag, data_time), 'r') as blog_file:
            blog_url_lst = blog_file.read()

        request = Request(request_header(), dict(eval(get_cookie())))
        count = 0
        for blog_url in eval(blog_url_lst):
            try:
                count += 1
                if count >= 20:
                    count = 0
                    print('累计请求20次,线程暂停60秒后,切换IP继续执行...')
                    # cutover_proxy()
                    time.sleep(60)

                resp = request.get_blog_page(blog_url)
                if resp.status_code == 200 and resp.url == blog_url+'/':

                    html = resp.text
                    user_blog_info = {}
                    #设置hashTag
                    user_blog_info["hashTag"] = tag

                    #设置HomePageName
                    patter_home_page_name =  re.compile(r'"alternateName":"@(.*?)"')
                    home_page_name_data = re.findall(patter_home_page_name, html)
                    if len(home_page_name_data) > 0:
                        home_page_name = str(home_page_name_data[0])
                        user_blog_info["homePageName"] = home_page_name
                    else:
                        user_blog_info["homePageName"] = ''

                    # 获取帖子数
                    patter_posts = re.compile(r'"edge_owner_to_timeline_media":{"count":(.*?),')
                    posts_data = re.findall(patter_posts, html)
                    if len(posts_data) > 0:
                        posts = eval(posts_data[0])
                        user_blog_info["posts"] = posts
                    else:
                        user_blog_info["posts"] = ''
                    # 获取粉丝数
                    patter_fans = re.compile(r'"userInteractionCount":(.*?)}')
                    fans_data = re.findall(patter_fans, html)
                    if len(fans_data) > 0:
                        fans = eval(fans_data[0])
                        user_blog_info["fans"] = fans
                    else:
                        user_blog_info["fans"] = ''
                    # 获取关注数
                    patter_focus = re.compile(r'"edge_follow":{"count":(.*?)}')
                    focus_data = re.findall(patter_focus, html)
                    if len(focus_data) > 0:
                        focus = eval(focus_data[0])
                        user_blog_info["focus"] = focus
                    else:
                        user_blog_info["focus"] = ''

                    # 获取用户名称
                    patter_username = re.compile(r'"follows_viewer":false,"full_name":"(.*?)",')
                    username_data = re.findall(patter_username, html)
                    if len(username_data) > 0:
                        username = username_data[0]
                        user_blog_info["username"] = username.encode('utf-8', 'ignore').decode('unicode_escape')
                    else:
                        user_blog_info["username"] = ''

                    # 获取用户类别
                    patter_category = re.compile(r'"category_enum":"(.*?)",')
                    category_data = re.findall(patter_category, html)
                    if len(category_data) > 0:
                        category = category_data[0]
                        user_blog_info["profession"] = category
                    else:
                        user_blog_info["profession"] = ''

                    # 获取用户描述信息
                    patter_biography = re.compile(r'"user":{"biography":"(.*?)","blocked_by_viewer"')
                    biography_data = re.findall(patter_biography, html)
                    if len(biography_data) > 0:
                        biography = biography_data[0]
                        user_blog_info["description"] = biography.encode('utf-8', 'ignore').decode('unicode_escape')
                    else:
                        user_blog_info["description"] = ''

                    # 获取用户高清照片信息
                    patter_pic_url_hd = re.compile(r'"profile_pic_url_hd":(.*?),"should_show_category"')
                    pic_url_hd_data = re.findall(patter_pic_url_hd, html)
                    if len(pic_url_hd_data)>0:
                        pic_url_hd = pic_url_hd_data[0]
                        pic_url_hd = pic_url_hd.replace('\\u0026','&')
                        print('pic_url_hd', pic_url_hd)
                        pic_url_hd_list.append(pic_url_hd)

                    print('user_blog_info', user_blog_info)
                    user_blog_list.append(user_blog_info)
                else:
                    print('账户行为异常,请确认账户状态是否正常','tag=', tag,'blog_url=', blog_url, 'status_code=',
                          resp.status_code, 'reason=', resp.reason)

            except requests.RequestException:
                print("SSLException", traceback.print_exc())
                print('切换新的ip,休眠60秒后执行....')
                # 切换可用的新IP
                cutover_proxy()
                time.sleep(60)


        print('user_blog_list:', user_blog_list)
        print('pic_url_hd_list',pic_url_hd_list)

        if len(user_blog_list) > 0:
            # 循环列表写入数据到文件中
            write_path = os.path.expandvars('$HOME')+'/tmp'
            with open('{0}/{1}-blog-{2}.json'.format(write_path,tag, data_time), 'a') as blog_file:
                for user_log in user_blog_list:
                    blog_file.write(str(user_log))
                    blog_file.write('\n')

            with open('{0}/{1}-img-blog-{2}.json'.format(write_path, tag, data_time), 'a') as img_blog_file:
                for pic_url_hd in pic_url_hd_list:
                    img_blog_file.write(str(pic_url_hd))
                    img_blog_file.write('\n')

    except FileNotFoundError:
        print('with open file exception:', traceback.print_exc())


if __name__ == '__main__':
    tag = 'smok'
    access_blog_page(tag)
    pass
