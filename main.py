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

def WorkOnPage(title):
    print("Working on {}".format(title))
    edit_token_data = PerformAPIGetActions(S,{
        'action':"query",
        'meta':"tokens",
        'type':"csrf",
        'format':"json",
        'curtimestamp':True,
    })
    edit_token = edit_token_data['query']['tokens']['csrftoken']
    starttimestamp = edit_token_data["curtimestamp"]
    page_data = PerformAPIGetActions(S,{
        "action":"query",
        "prop":"revisions",
        "titles":title,
        "rvslots":"*",
        "rvprop":"content|timestamp",
        "formatversion":"2",
        'format':"json"
    })
    try:
        TS = page_data["query"]["pages"][0]["revisions"][0]["timestamp"]
    except KeyError:
        print("Page not exist or timestamp invalid in {}".format(title))
        return
    page_content = page_data["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]
    page_modifyed_data = page_content
    for x,y in config["replaces"].items():
        print("Working on '{}' to '{}'".format(x,y))
        page_modifyed_data = page_modifyed_data.replace(x,y)
    
    PerformAPIPostActions(S,{
        "action": "edit",
        "title": title,
        "token": edit_token,
        "format": "json",
        "text": page_modifyed_data,
        "summary":config["summary"],
        "bot": True,
        "headers":{'Content-Type': 'multipart/form-data'},
        "basetimestamp":TS,
        "starttimestamp":starttimestamp,
    })
    

if len(sys.argv) == 2:
    print("Working on spec page `{}`".format(sys.argv[1]))
    WorkOnPage(sys.argv[1])
else:
    while True:
        print("not provide title, do in random pages")
        pageTitle = PerformAPIGetActions(S,{
            "action":"query",
            "list":"random",
            "rnlimit":1,
            "utf8":"",
            "format":"json",
        })["query"]["random"][0]["title"]
        print("Working on {}".format(pageTitle))
        WorkOnPage(pageTitle)
        time.sleep(config["delay"])

    




    

