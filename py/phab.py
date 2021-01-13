import re
import os
import sys
from pprint import pprint
import argparse
from io import BytesIO, SEEK_SET

import frontmatter
from frontmatter.default_handlers import YAMLHandler
from phabricator import Phabricator

cmd = sys.argv[1]
task = sys.argv[2]
arg = sys.argv[3]

phab = Phabricator();
phab.update_interfaces()

def task_string_to_id(tname):
    return int(tname[1:])

transactions = []
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

def task_get_revision_phids(task_name):
    phids = []
    result = phab.edge.search(sourcePHIDs=[task_name], types=["task.revision"])
    for item in result.data:
        phids.append(item['destinationPHID'])

    return phids

def task_get_revisions(task_name):
    revs = []
    phids = task_get_revision_phids(task_name)
    revisions = phab.differential.revision.search(constraints={'phids': phids})
    if revisions:
        for rev in revisions['data']:
            revs.append("D{}".format(rev['id']))

    return revs, revisions

def revision_get_diff_phid(revision):
    revid = int(revision[1:])
    revs = phab.differential.revision.search(constraints={'ids': [revid]})
    phid = revs['data'][0]['fields']['diffPHID']
    return phid

def update():
    description=""

    with open(arg, 'r') as fp:
        post = frontmatter.load(fp)

        if post.content.strip().endswith('+++'):
            content = post.content.rsplit("+++", 2)
            backmatter = content[1]
            content = content[0]
        else:
            content = post.content
            backmatter = None

        pprint(backmatter)

        description = vimwiki2phab(content)

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

def strike(text):
    result = ''
    for c in text:
        result = result + c + '\u0336'
    return result

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
        if(t['authorPHID']):
            post['author'] = phid2user(t['authorPHID'])
        f = BytesIO()
        frontmatter.dump(post, f)
        fp.seek(0, SEEK_SET)
        fp.write(f.getvalue().decode('utf-8'))
        fp.write(os.linesep)
        fp.write(os.linesep)

        fp.write('+++\n')

        backmatter = []
        _, revisions = task_get_revisions(task)
        for rev in revisions['data']:
            rname = "D{}".format(rev['id'])
            title = rev['fields']['title']
            closed = rev['fields']['status']['closed']
            if(closed):
                title = strike(title)

            backmatter.append("{} - {}".format(rname, title))

        pprint(backmatter)
        fp.write("\n".join(backmatter))

        fp.write('\n+++\n')
        fp.write(os.linesep)


def get_task(t_name):
    return phab.maniphest.query(ids=[task_string_to_id(task)])

def get_task_phid(t_name):
    t = get_task(t_name)
    if t:
        return list(t)[0]
    return None

def query():
    t = get_task(task)
    key = list(t)[0]
    pprint(t[key])


def revisions():
    revs, _ = task_get_revisions(task)
    for rev in revs:
        print(rev.strip(), end=' ')

    print()

def diff(diff_name):
    phid = revision_get_diff_phid(diff_name)
    diff = phab.differential.diff.search(constraints={'phids': [phid]})
    diffid = diff['data'][0]['id']
    rawdiff = phab.differential.getrawdiff(diffID="{}".format(diffid))
    print(rawdiff[:])

def diff_approve(diff_name):
    transactions.append({'type': 'accept', 'value': True})
    print(diff_name, transactions)
    result = phab.differential.revision.edit(objectIdentifier=diff_name, transactions=transactions)
    pprint(result)

def comments():
    t = phab.transaction.search(objectIdentifier="T31334")#phab.maniphest.query(ids=[task_string_to_id(task)])
    key = list(t)[0]
    pprint(t[key])

def comment():
    transactions=[]
    phab.maniphest.edit(objectIdentifier=task, transactions=transactions)

def create():
    tid = phab.maniphest.createtask(title=arg)
    print('T'+tid['id']+'.md')

if cmd == "update":
    update()

if cmd == "sync":
    sync()

if cmd == "create":
    create()

if cmd == "query":
    query()

if cmd == "diff":
    diff(task)

if cmd == "diff-approve":
    diff_approve(task)

if cmd == "comments":
    comments()

if cmd == "revisions":
    revisions()
