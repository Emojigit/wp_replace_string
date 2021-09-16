#!/usr/bin/python3
# -*- coding: utf-8 -*-
import requests, sys, time, json
S = requests.Session()
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print("`config.txt not exits!")
    exit(1)
except json.decoder.JSONDecodeError:
    print("Syntax ERROR! Prasing traceback below.")
    raise
if ("replaces" not in config) or len(config) == 0:
    print("No replacing rules!")
    exit(2)
elif "api_php" not in config:
    print("`api_php` key not found!")
    exit(2)
elif "api_php" not in config:
    print("`api_php` key not found!")
    exit(2)
elif "username" not in config:
    print("`username` key not found!")
    exit(2)
elif "botpassword" not in config:
    print("`botpassword` key not found!")
    exit(2)
elif "summary" not in config:
    print("`summary` key not found!")
    exit(2)
elif "delay" not in config:
    print("`delay` key not found, fallback to default (10).")
    config["delay"] = 10

def PerformAPIGetActions(Session, args):
    args["format"] = "json"
    R = Session.get(url=config["api_php"], params=args)
    print(R.text)
    return R.json()

def PerformAPIPostActions(Session, args):
    args["format"] = "json"
    R = Session.post(url=config["api_php"], data=args)
    print(R.text)
    return R.json()

login_token = PerformAPIGetActions(S,{
    'action':"query",
    'meta':"tokens",
    'type':"login",
    'format':"json",
})['query']['tokens']['logintoken']

login_table = PerformAPIPostActions(S,{
    'action':"login",
    'lgname':config["username"],
    'lgpassword':config["botpassword"],
    'lgtoken':login_token,
    'format':"json",
})
login_result = login_table["login"]["result"]
login_username = login_table["login"]["lgusername"]

if login_result == "Success":
    print("Logged in as {}".format(login_username))
else:
    print("Login failed")
    exit(3)




    

