import re
import traceback
import time
import os
from fake_useragent import UserAgent
from .request import RequestConfig as req,cutover_proxy

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


    def get_sections(self,form):
        return req.req_session().post(f'https://i.instagram.com/api/v1/tags/{self.tag}/sections/', headers=self.headers,
                                     data=form.data, cookies=self.cookies, timeout=30)

    def get_tag_page(self, url):
        return req.req_session().get(f'{url}' + self.tag + '/', headers=self.headers, cookies=self.cookies)


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

            form = Form(max_id=next_max_id, page=next_page,media_ids=next_media_ids)
            result = cycle_get_section_data(request,form)
            '''
            请求计数:
                访问10次接口 等待30秒
            '''
            count +=1
            if count>=20:
                #访问10次接口,停30秒
                count = 0
                print('累计请求20次,线程暂停60秒后,切换IP继续执行...')
                cutover_proxy() # 切换新的ip爬取数据
                time.sleep(60)



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
                print(result)
                break
        else:
            print('循环获取section data 结束.....')

        # 循环结束,把获取到的所有blog_url 保存到 {$tag}-blog-url-{$datatime}.txt
        data_time = time.strftime("%Y-%m-%d", time.localtime())
        write_path = os.path.expandvars('$HOME') + '/tmp'
        with open('{0}/{1}-blog-url-{2}.txt'.format(write_path,tag, data_time), 'w') as blog_url_file:
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


def cycle_get_section_data(request,form):
    try:

        req_section = request.get_sections(form)
        if req_section.status_code == 200:
            try:
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


            except:
                print('json parse exception:', traceback.print_exc())
                # 切换可用的新IP
                cutover_proxy()
                return dict({})

        else:
            return dict({
                'status': req_section.status_code,
                'reason': req_section.reason,
                'text': req_section.text
            })
    except:
        print('ssl exception:',traceback.print_exc())
        #切换可用的新IP
        cutover_proxy()
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
