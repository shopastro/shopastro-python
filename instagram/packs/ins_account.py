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
            print('没有可用的账号资源,请检查账号状态,并重新维护账号信息...30秒后重新检查资源')
            time.sleep(30)
            # 重新加载文件,并读取账号信息
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

# class Account:
#     _instance = None
#     flag = False
#
#     def __init__(self):
#         if Account.flag:
#             return
#         self.__get_ins_account()
#         Account.flag = True
#
#     def __new__(cls, *args, **kwargs):
#         if not cls._instance:
#             """如果没有实例"""
#             cls._instance = object.__new__(cls)
#         return cls._instance
#
#     @staticmethod
#     def get_valid_account():
#         global account_list
#         while True:
#             if len(account_list) > 0:
#                 account = account_list.pop(0)
#                 if account["state"] == 'alive':
#                     return account
#             else:
#                 print('没有可用的账号资源,请检查账号状态,并重新维护账号信息...30秒后重新检查资源')
#                 time.sleep(30)
#                 # 重新加载文件,并读取账号信息
#                 account_list = Account.__get_ins_account()
#
#     def __get_ins_account(self):
#         global account_list
#         while True:
#             if os.path.exists("../user_account.json"):
#                 try:
#                     with open('../user_account.json') as account_file:
#                         accounts_json = json.loads(account_file.read().strip())
#                 except Exception:
#                     print('exception:', traceback.print_exc())
#                     print('读取账号资源错误,请检查user_account.json文件中,账号格式是否有误....')
#                     continue
#                 account_list = accounts_json["account_params"]
#                 return account_list
#             else:
#                 print("严重警告：当前无instagram账号资源，等待资源添加中...")
#                 time.sleep(120)
#
#     @staticmethod
#     def update_account_status(state):
#         global account
#         with open('../user_account.json') as account_file:
#             accounts_json = json.loads(account_file.read().strip())
#         account_params = accounts_json["account_params"]
#         accounts_json_new = dict()
#         account_params_new = list()
#         for account_param in account_params:
#             if account_param["account"] == account["account"]:
#                 account_param["state"] = state
#
#             account_params_new.append(account_param)
#             accounts_json_new["account_params"] = account_params_new
#         with open("../user_account.json", "w", encoding="utf-8") as f_new:
#             f_new.write(json.dumps(accounts_json_new, ensure_ascii=False))
