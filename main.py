#!/usr/bin/python3
# -*- coding: utf-8 -*-
import requests, sys, time, json, re, subprocess
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
if (len(config) == 0) or (("replaces" not in config) and ("replaces_regex" not in config)):
    print("No replacing rules!")
    exit(2)
elif "replaces" not in config:
    config["replaces"] = {}
elif "replaces_regex" not in config:
    config["replaces_regex"] = {}
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
if "delay" not in config:
    print("`delay` key not found, fallback to default (10).")
    config["delay"] = 10
if "find_method" not in config:
    print("`find_method` key not found, fallback to default (random).")
    config["find_method"] = "random"
elif config["find_method"] != "random" and config["find_method"] != "exturlusage":
    print("Find method unknown!")
    exit(2)
elif config["find_method"] == "exturlusage" and ("m_exturlusage_defs" not in config):
    print("`m_exturlusage_defs` key not found while the method is `exturlusage`!")
    exit(2)
if "skipped_ns" not in config:
    print("`skipped_ns` key not found, fallback to default (None).")
    config["skipped_ns"] = []


def PerformAPIGetActions(Session, args):
    args["format"] = "json"
    args["utf8"] = True
    R = Session.get(url=config["api_php"], params=args)
    print(R.text)
    return R.json()

def PerformAPIPostActions(Session, args):
    args["format"] = "json"
    args["utf8"] = True
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

def WorkOnPage(title,bot):
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
    if title.find(":") and title.split(":",1) == "Topic": # Flow
        print("flow discussion functtion not complete")
        return
    else: # Plain Text (e.g. Wikitext, Lua)
        flow_header_data = PerformAPIGetActions(S,{
            "action": "flow",
            "format": "json",
            "submodule": "view-header",
            "page": title,
            "vhformat": "wikitext"
        })
        is_flow = False
        try: # In case the "plain text" is the talk page itself instead of topic
            is_flow = True if flow_header_data["flow"] else False
        except KeyError:
            pass
        page_data = PerformAPIGetActions(S,{
            "action":"query",
            "prop":"revisions",
            "titles":title,
            "rvslots":"*",
            "rvprop":"content|timestamp",
            "formatversion":"2",
            "format":"json"
        })    
        try:
            TS = page_data["query"]["pages"][0]["revisions"][0]["timestamp"]
        except KeyError:
            print("Page not exist or timestamp invalid in {}".format(title))
            return
        if is_flow:
            try:
                page_content = ehprev_revision = flow_header_data["flow"]["view-header"]["result"]["header"]["revision"]["content"]["content"]
                ehprev_revision = flow_header_data["flow"]["view-header"]["result"]["header"]["revision"]["revisionId"]
            except KeyError:
                print("No header or created wrong page!")
                return
        else:
            page_content = page_data["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]
        print(page_content)
        page_modiflyed_data = page_content
        for x,y in config["replaces"].items():
            print("Working on '{}' to '{}'".format(x,y))
            page_modiflyed_data = page_modiflyed_data.replace(x,y)
        for x,y in config["replaces_regex"].items():
            print("Working on regex '{}' to '{}'".format(x,y))
            page_modiflyed_data = re.sub(x,y,page_modiflyed_data)
        
        if page_content == page_modiflyed_data:
            print("No diff, skip perform edit!")
            return
        if not is_flow:
            PerformAPIPostActions(S,{
                "action": "edit",
                "title": title,
                "token": edit_token,
                "format": "json",
                "text": page_modiflyed_data,
                "summary":config["summary"] + (" (Manual)" if not bot else ""),
                "bot": bot,
                "headers":{'Content-Type': 'multipart/form-data'},
                "basetimestamp":TS,
                "starttimestamp":starttimestamp,
            })
        else:
            PerformAPIPostActions(S,{
                "action": "flow",
                "submodule": "edit-header",
                "page": title,
                "token": edit_token,
                "ehprev_revision": ehprev_revision,
                "ehcontent": page_modiflyed_data,
                "headers":{'Content-Type': 'multipart/form-data'}
            })
    

if len(sys.argv) == 2:
    print("Working on spec page `{}`".format(sys.argv[1]))
    WorkOnPage(sys.argv[1],False)
else:
    while True:
        if "noauto" in config:
            print("Fuse enabled")
            exit(4)
        print("not provide title, enter automatic mode")
        if config["find_method"] == "random":
            pageTitle = PerformAPIGetActions(S,{
                "action":"query",
                "list":"random",
                "rnlimit":1,
                "utf8":"",
                "format":"json",
            })["query"]["random"][0]["title"]
            print("Working on {}".format(pageTitle))
            WorkOnPage(pageTitle,True)
            time.sleep(config["delay"])
        elif config["find_method"] == "exturlusage":
            pageTitles = PerformAPIGetActions(S,{
                "action":"query",
                "list":"exturlusage",
                "euquery":config["m_exturlusage_defs"]["euquery"],
                "eulimit":config["m_exturlusage_defs"]["eulimit"],
                "euprotocol":config["m_exturlusage_defs"]["euprotocol"],
                "utf8":"",
                "format":"json",
            })["query"]["exturlusage"]
            for x in pageTitles:
                print("Working on {}".format(x["title"]))
                if x["ns"] in config["skipped_ns"]:
                    print("Matched NS {}, not process!".format(str(x["ns"])))
                else:
                    WorkOnPage(x["title"],True)
                    time.sleep(config["delay"])
            time.sleep(10)

    




    

