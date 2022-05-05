import os
import json
import time
import traceback

'''
    这个一个单例的类,全局唯一
'''


# 全局属性初始化前需要调用的函数
def get_ins_account():
    while True:
        if os.path.exists("../user_account.json"):
            try:
                with open('../user_account.json') as account_file:
                    accounts_json = json.loads(account_file.read().strip())
            except Exception:
                print('exception:', traceback.print_exc())
                print('读取账号资源错误,请检查user_account.json文件中,账号格式是否有误....')
                continue
            account_list = accounts_json["account_params"]
            return account_list
        else:
            print("严重警告：当前无instagram账号资源，等待资源添加中...")
            time.sleep(120)


account = dict()
account_list = get_ins_account()


def get_valid_account():
    global account
    global account_list
    while True:
        if len(account_list) > 0:
            account = account_list.pop(0)
            if account["state"] == 'alive':
                return account
        else:
            '''
                先读取资源中是否存在状态是alive的账户
                    账户不存在休眠30秒后重新读取
                    存在返回list
                
            '''

            if len(account_list) == 0:
                print('正在检查是否还有可用账号资源....')
                time.sleep(30)
                account_list = get_ins_account()




def update_account_status(state):
    global account
    with open('../user_account.json') as account_file:
        accounts_json = json.loads(account_file.read().strip())
    account_params = accounts_json["account_params"]
    accounts_json_new = dict()
    account_params_new = list()
    for account_param in account_params:
        if account_param["account"] == account["account"]:
            account_param["state"] = state

        account_params_new.append(account_param)
        accounts_json_new["account_params"] = account_params_new
    with open("../user_account.json", "w", encoding="utf-8") as f_new:
        f_new.write(json.dumps(accounts_json_new, ensure_ascii=False))
