import json
import re
import traceback
import time
import os

import requests
from .ins_account import update_account_status
from fake_useragent import UserAgent
from .request import RequestConfig as reqc, cutover_proxy
from lxml import etree
from .ins_login import login_and_check

sleep_second = 120

class Form:

    def __init__(self, max_id, media_ids, page, include_persistent=0, surface='grid', tab='recent'):
        self.max_id = max_id
        self.media_ids = media_ids
        self.page = page
        self.include_persistent = include_persistent
        self.surface = surface
        self.tab = tab

    @property
    def data(self):
        return (dict(
            {
                'include_persistent': self.include_persistent,
                'max_id': self.max_id,
                'next_media_ids': self.media_ids,
                'page': self.page,
                'surface': self.surface,
                'tab': self.tab
            }
        ))

    def __len__(self):
        return len(repr(self.data))


class Request:

    def __init__(self, headers, cookies, tag):
        self.tag = tag
        self.headers = headers
        self.cookies = cookies

    def get_sections(self, form):
        return reqc.req_session().post(f'https://i.instagram.com/api/v1/tags/{self.tag}/sections/',
                                       headers=self.headers,
                                       data=form.data, cookies=self.cookies, timeout=30)

    def get_tag_page(self, url):
        return reqc.req_session().get(f'{url}' + self.tag + '/', headers=self.headers, cookies=self.cookies)

    def get_checkpoint_url(self, url):
        return reqc.req_session().get(f'{url}', headers=self.headers, cookies=self.cookies)


def request_header():
    headers = {
        'User-Agent': UserAgent().Chrome,  # 谷歌浏览器
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'X-Csrftoken': '',
        'x-ig-app-id': '936619743392459',
        'Origin': 'https://www.instagram.com',
        'Referer': 'https://www.instagram.com/',
        'Connection': 'close'
    }

    return headers


def get_cookie():
    with open('../cookies.txt', 'r') as file:
        return file.read()


def access_tag_page(tag, url="https://www.instagram.com/explore/tags/"):
    global sleep_second
    headers = request_header()
    cookies = dict(eval(get_cookie()))
    headers['X-Csrftoken'] = cookies.get('csrftoken')
    request = Request(headers=headers, cookies=cookies, tag=tag)
    req = request.get_tag_page(url)
    if req.status_code == 200:
        html = req.text
        patter = re.compile(r'"next_max_id":"(.*?)","next_page":(.*?),"next_media_ids":(.*?)}')
        list_data = re.findall(patter, html)

        next_max_id = ''
        next_page = ''
        next_media_ids = []
        for tuple_data in list_data:
            id = tuple_data[0]
            if len(id) > len(next_max_id):
                next_max_id = id
                next_page = tuple_data[1]
                next_media_ids = tuple_data[2]
            else:
                break

        all_blog_url_list = []
        next_page = 1
        count = 0
        while next_page >= 1:
            # random_second = random.randint(2, 5)
            # print('程序休眠', str(random_second) + 's')
            # time.sleep(random_second)

            form = Form(max_id=next_max_id, page=next_page, media_ids=next_media_ids)
            result = cycle_get_section_data(request, form)
            try:

                if 'data' in result:
                    section_data = result.get('data')
                    next_max_id = section_data.get('next_max_id')
                    next_page = section_data.get('next_page')
                    next_media_ids = str(list(map(int, section_data.get('next_media_ids'))))
                    blog_url_list = section_data.get('blog_url_list')
                    sections = section_data.get('sections')
                    all_blog_url_list.extend(blog_url_list)
                    print(all_blog_url_list)
                    if sections == []:  # sections 为[] 代表翻页到底了
                        break
                else:
                    print(all_blog_url_list)
            except Exception:
                print('exception', traceback.print_exc())
                break
            '''
                请求计数:
                访问20次接口 等待120秒
            '''
            count += 1
            if count >= 20:
                # 访问10次接口,停30秒
                count = 0
                print('累计请求20次,线程暂停{0}秒后,切换IP继续执行...'.format(sleep_second))
                cutover_proxy()  # 切换新的ip爬取数据
                time.sleep(sleep_second)
            else:
                pass

        else:
            print('循环获取section data 结束.....')

        # 循环结束,把获取到的所有blog_url 保存到 {$tag}-blog-url-{$datatime}.txt
        data_time = time.strftime("%Y-%m-%d", time.localtime())
        write_path = os.path.expandvars('$HOME') + '/tmp'
        with open('{0}/{1}-blog-url-{2}.txt'.format(write_path, tag, data_time), 'w') as blog_url_file:
            blog_url_file.write(str(all_blog_url_list))

        # url保存成功后,返回数据,执行访问blog页面流程
        data = dict({
            'blog_url_list': all_blog_url_list
        })

        return dict({
            'status': req.status_code,
            'reason': req.reason,
            'text': req.text,
            'data': data
        })


    else:
        return dict({
            'status': req.status_code,
            'reason': req.reason,
            'text': req.text
        })


def cycle_get_section_data(request, form):
    try:

        req_section = request.get_sections(form)

        if req_section.status_code == 200:
            dict_json = req_section.json()
            sections = dict_json.get('sections')
            data = dict({
                'next_max_id': dict_json.get('next_max_id'),
                'next_page': dict_json.get('next_page'),
                'next_media_ids': dict_json.get('next_media_ids'),
                'blog_url_list': resolve_section_data(sections),
                'sections': sections
            })

            return dict({
                'status': req_section.status_code,
                'reason': req_section.reason,
                'text': req_section.text,
                'data': data
            })
        else:
            if "https://i.instagram.com/challenge/?next=" in req_section.text:
                result_json = json.loads(req_section.text)
                # 账户被检测到机器人行为,修改当前账户状态,并更换新的账户爬取
                if result_json.get("lock") == True and result_json.get("status") == "fail":
                    print('账户被检测到有状态异常,正在切换至新的账户...休眠{0}秒后执行'.format(sleep_second))
                    update_account_status("sleep")
                    # 校验并重新登录新的账号进行操作
                    login_and_check()
                    time.sleep(sleep_second)

            elif req_section.status_code == 429:
                print('请求过于频繁,切换ip和账号并在10分钟后,重新爬取...')
                login_and_check()
                cutover_proxy()
                time.sleep(600)


            return dict({
                'status': req_section.status_code,
                'reason': req_section.reason,
                'text': req_section.text
            })

    except json.JSONDecodeError:
        # 获取response中的html元素信息,判断当前页面是否重定向到登录页
        html_text = req_section.text.encode('utf-8')
        html = etree.HTML(html_text)
        html_result = html.xpath('/html[contains(@class,"logged-in")]')
        if html_result:
            # 校验并重新登录新的账号进行操作
            print('正在切换新的账号.......')
            login_and_check()
        return dict({})

    except requests.RequestException:
        print('ssl exception:', traceback.print_exc())
        print('切换新的ip,休眠{0}秒后执行....'.format(sleep_second))
        # 切换可用的新IP
        cutover_proxy()
        time.sleep(sleep_second)
        return dict({})


def resolve_section_data(sections):
    blog_url_list = []
    for section in sections:
        layout_content = section.get('layout_content')
        medias = layout_content.get('medias')
        for media in medias:
            media_data = media.get('media')
            try:
                comment_count = int(media_data.get('comment_count', 0))
                like_count = int(media_data.get('like_count', 0))
            except TypeError:
                print('typeError exception:', traceback.print_exc())

            if comment_count + like_count >= 300:
                user = media_data.get('user')
                username = user.get('username')
                blog_url_list.append('https://www.instagram.com/' + username)

    return blog_url_list


if __name__ == '__main__':
    tag = 'smok'
    tag_result = access_tag_page(tag)
    print(tag_result)
