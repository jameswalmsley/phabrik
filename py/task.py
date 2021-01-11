import re
import os
import sys
import argparse
from io import BytesIO, SEEK_SET

import frontmatter
from phabricator import Phabricator

cmd = sys.argv[1]
task = sys.argv[2]
arg = sys.argv[3]

if not task.startswith('T'):
    print("Error invalid task number -> begin with Txxxxx")
    exit(1)

transactions = []
phab = Phabricator();

def task_string_to_id(tname):
    return int(tname[1:])

def add_transaction(type, value):
    transactions.append({'type': type, 'value': value})

def vimwiki2phab(md):
    out = ""
    for line in md.splitlines():
        matches = re.findall('(\[\[T\d+\]\])', line)
        if matches:
            for t in matches:
                line = line.replace(t, t.replace('[','').replace(']', ''))
        out = out + line + os.linesep

    return out

def phab2vimwiki(input):
    md = ""
    for line in input.splitlines():
        matches = re.findall('(T\d+)', line)
        if len(matches) > 0:
            for t in matches:
                line = line.replace(t, '[[' + t + ']]')
        md = md + line + os.linesep

    return md


def update():
    description=""

    with open(arg, 'r') as fp:
        post = frontmatter.load(fp)

        description = vimwiki2phab(post.content)

        add_transaction('description', description)

        if('title' in post):
                add_transaction('title', post['title'])

        if('points' in post):
                add_transaction('points', post['points'])

        if('assigned' in post):
                username = post['assigned']
                users = phab.user.find(aliases=[username])
                if(username in users):
                    add_transaction('owner', users[username])

        phab.maniphest.edit(objectIdentifier=task, transactions=transactions)

def phid2user(phid):
    uid = phab.user.query(phids=[phid])
    return uid[0]['userName']


def sync():
    t = phab.maniphest.query(ids=[task_string_to_id(task)])
    if(len(t) != 1):
        print("error: Found more than 1 task.")

    key = list(t)[0]
    t = t[key]

    post = None
    with open(arg, 'r') as fp:
        post = frontmatter.load(fp)


    with open(arg, 'w+') as fp:
        post.content = phab2vimwiki(t['description'])
        if(t['ownerPHID']):
            post['assigned'] = phid2user(t['ownerPHID'])
        print(t)
        if(t['authorPHID']):
            post['author'] = phid2user(t['authorPHID'])
        f = BytesIO()
        frontmatter.dump(post, f)
        fp.seek(0, SEEK_SET)
        fp.write(f.getvalue().decode('utf-8'))
        fp.write(os.linesep)
        fp.write(os.linesep)

def create():
    tid = phab.maniphest.createtask(title=arg)
    print('T'+tid['id']+'.md')

if cmd == "update":
    update()

if cmd == "sync":
    sync()

if cmd == "create":
    create()

