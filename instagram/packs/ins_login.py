import re
import pickle
from datetime import datetime

import requests
from fake_useragent import UserAgent

from .ins_account import get_valid_account,update_account_status
from .request import RequestConfig as reqc


def request_header():
    headers = {
        'User-Agent': UserAgent().Chrome  # 谷歌浏览器
    }
    return headers


class Token:

    def __init__(self, URL):
        self.url = URL

    def __call__(self, *args, **kwargs):
        return self.url(*args, **kwargs)


class Form:

    def __init__(self, User, Pass):
        self.User = User
        self.Pass = Pass

    @Token
    def cookie(url="https://www.instagram.com/"):
        resp = reqc.req_session().get(f'{url}', headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux armv8l; rv:78.0) Gecko/20100101 Firefox/78.0"}, verify=False)
        print('get_cookie_resp', resp.content)
        cookies = dict(resp.cookies)

        return cookies

    @property
    def data(self):
        return (dict(
            {
                'username': self.User,
                'enc_password': "#PWD_INSTAGRAM_BROWSER:0:%s:%s" % (int(datetime.now().timestamp()), self.Pass),
            },
            **pickle.loads(
                b'\x80\x03}q\x00(X\x0b\x00\x00\x00queryParamsq\x01X\x02\x00\x00\x00{}q\x02X\r\x00\x00\x00optIntoOneTapq\x03X\x05\x00\x00\x00falseq\x04X\x11\x00\x00\x00stopDeletionNonceq\x05X\x00\x00\x00\x00q\x06X\x14\x00\x00\x00trustedDeviceRecordsq\x07h\x02u.'
            )
        ))

    def __len__(self):
        return len(repr(self.data))

    def header(self):
        return b'\x80\x03}q\x00(X\x04\x00\x00\x00Hostq\x01X\x11\x00\x00\x00www.instagram.comq\x02X\n\x00\x00\x00User-Agentq\x03XD\x00\x00\x00Mozilla/5.0 (X11; Linux armv8l; rv:78.0) Gecko/20100101 Firefox/78.0q\x04X\x06\x00\x00\x00Acceptq\x05X\x03\x00\x00\x00*/*q\x06X\x0f\x00\x00\x00Accept-Languageq\x07X\x0e\x00\x00\x00en-US,en;q=0.5q\x08X\x0f\x00\x00\x00Accept-Encodingq\tX\x11\x00\x00\x00gzip, deflate, brq\nX\x0c\x00\x00\x00Content-Typeq\x0bX!\x00\x00\x00application/x-www-form-urlencodedq\x0cX\x10\x00\x00\x00X-Requested-Withq\rX\x0e\x00\x00\x00XMLHttpRequestq\x0eX\x06\x00\x00\x00Originq\x0fX\x19\x00\x00\x00https://www.instagram.comq\x10X\x03\x00\x00\x00DNTq\x11X\x01\x00\x00\x001q\x12X\n\x00\x00\x00Connectionq\x13X\n\x00\x00\x00keep-aliveq\x14X\x07\x00\x00\x00Refererq\x15X\x1a\x00\x00\x00https://www.instagram.com/q\x16u.'

    @property
    def items(self):
        cc = self.cookie()
        return (cc['csrftoken'], re.sub("': '", "=", str(cc)[2:-2]).replace("', '", "; "))


class LoginRequest(Form):

    def __init__(self, account_param):
        super(LoginRequest, self).__init__(account_param["account"], account_param["password"])

    def headers(self):
        item = self.items

        return (dict({
            "X-CSRFToken": item[0],
            "Content-Length": f"{self.__len__()}",
            "Cookie": item[1]
        },
            **pickle.loads(self.header())
        ))

    @property
    def login(self):

        resp = reqc.req_session().post("https://www.instagram.com/accounts/login/ajax/",
                                       headers=self.headers(), data=self.data, verify=False,timeout=10)
        return (
            {
                'auth': resp.json().get('authenticated'),
                'cookies': dict(resp.cookies)
            }
        )

    def check_auth(self):
        log = self.login
        if log.get('auth') == 1:
            with open("../cookies.txt", "w") as ck:
                ck.write(str(log.get("cookies")))
            return "Logged in Successfully"
        else:
            return "Incorrect password"


def login_and_check():
    while True:
        account = get_valid_account()
        for i in range(4):
            login_request = LoginRequest(account)
            try:
                login_request.login
                login_result = login_request.check_auth()
                print(login_result)
                if login_result == "Logged in Successfully":
                    return True
                else:
                    # 重试登录
                    print('登录失败,正在进行第' + str(i + 1) + '次重试....')
                    pass
            except requests.RequestException:
                print('连接超时,正在进行第' + str(i + 1) + '次重试....')

        else:
            print('3次登录失败,正在切换可用的账号,进行重新登录...')
            update_account_status('sleep')


if __name__ == '__main__':
   pass
