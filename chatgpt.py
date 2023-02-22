# -*- coding: utf-8 -*-

import time
import json
import logging
import requests
from uuid import uuid1

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 定义代理
proxies = {"https":""}

# 定义模型
model="text-davinci-002-render-sha"

# 定义Cookie参数
# 需要在cookie获取以下三个参数，_puid为plus会员专属，没它不行
_puid = ""
cf_clearance = ""
session_token = ""

headers = {
    'cookie': f'cf_clearance={cf_clearance}; _puid={_puid}; __Secure-next-auth.session-token={session_token}',
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
}

def get_authorization():
    # 获取accessToken，headers必须
    url = "https://chat.openai.com/api/auth/session"
    r = requests.get(url, headers=headers)
    authorization = r.json()["accessToken"]
    return "Bearer "+authorization

headers["authorization"] = get_authorization()

def get_latest_message_id(conversation_id):
    # 获取会话窗口最新消息id，连续对话必须
    url = f"https://chat.openai.com/backend-api/conversation/{conversation_id}"
    r = requests.get(url, headers=headers, proxies=proxies)
    return r.json()["current_node"]

def send_new_message(message):
    # 发送新会话窗口消息，返回会话id
    url = "https://chat.openai.com/backend-api/conversation"
    message_id = str(uuid1())
    data = {"action":"next","messages":[{"id":message_id,"role":"user","content":{"content_type":"text","parts":[message]}}],"parent_message_id":str(uuid1()),"model":model}
    r = requests.post(url, headers=headers, json=data, proxies=proxies)
    if r.status_code != 200:
        # 发送消息阻塞时等待20秒从新发送
        logging.warning(r.json()["detail"])
        time.sleep(20)
        return send_new_message(message)
    result = json.loads(r.text.split("data: ")[-2])
    text = "\n".join(result["message"]["content"]["parts"])
    conversation_id = result["conversation_id"]
    return text,conversation_id

def send_message(message, conversation_id):
    # 指定会话窗口发送连续对话消息
    url = "https://chat.openai.com/backend-api/conversation"
    # 获取会话窗口最新消息id
    message_id = get_latest_message_id(conversation_id)
    data = {"action":"next","messages":[{"id":str(uuid1()),"role":"user","content":{"content_type":"text","parts":[message]}}],"conversation_id":conversation_id,"parent_message_id":message_id,"model":model}
    r = requests.post(url, headers=headers, json=data, proxies=proxies)
    if r.status_code != 200:
        # 发送消息阻塞时等待20秒从新发送
        logging.warning(r.json()["detail"])
        time.sleep(20)
        return send_message(message, conversation_id)
    text = "\n".join(json.loads(r.text.split("data: ")[-2])["message"]["content"]["parts"])
    return text

if __name__ == "__main__":
    text,conversation_id = send_new_message("你是谁")
    text = send_message("我刚刚问你什么问题", conversation_id)
