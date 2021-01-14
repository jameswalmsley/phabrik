import os
import sys
import pathlib


from pprint import pprint
import argparse
from io import BytesIO, SEEK_SET

import frontmatter
from frontmatter.default_handlers import YAMLHandler
from phabricator import Phabricator

import utils
import model

utils.__init__()

spath = pathlib.Path(__file__).parent.absolute()

cmd = sys.argv[1]
task = sys.argv[2]
arg = sys.argv[3]

def update(task):
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

        description = utils.vimwiki2phab(content)

        t = model.Task(None)
        t.phid = utils.phid_lookup(task)
        t.description = description

        if('title' in post):
                t.title = post['title']
        if('points' in post):
                t.points = post['points']
        if('assigned' in post):
                t.assigned = post['assigned']

        t.commit()


def sync(task):
    t = model.Task.fromName(task)

    post = None
    with open(arg, 'r') as fp:
        post = frontmatter.load(fp)


    with open(arg, 'w+') as fp:
        post.content = utils.phab2vimwiki(t.description)
        if t.assigned:
            post['assigned'] = t.assigned.username
        post['author'] = t.author.username

        if t.points:
            post['points'] = t.points

        if t.projects:
            tags = []
            projects = []
            for proj in t.projects:
                if proj.slug:
                    tags.append(proj.slug.replace("_-_", "-"))
                else:
                    projects.append(proj.name.replace("_-_", "-"))
            post['tags'] = tags
            post['projects'] = projects

        if t.title:
            post['title'] = t.title

        f = BytesIO()
        frontmatter.dump(post, f)
        fp.seek(0, SEEK_SET)
        fp.write(f.getvalue().decode('utf-8'))
        fp.write(os.linesep)
        fp.write(os.linesep)

        fp.write('+++\n')

        backmatter = []
        for rev in t.revisions:
            status = utils.get_status_symbol(rev.status)
            title = rev.title
            if(rev.closed):
                title = utils.strike(title)
            backmatter.append("{} - {} - {}\n".format(rev.name, status, title))

        backmatter.append("\n" + (80*"=") + "\n")
        backmatter.append("Comments:\n")
        backmatter.append("" + (80*"=") + "\n\n")

        for comment in t.comments:
            if comment.removed:
                continue
            info = "{} wrote:".format(comment.author.username)
            created = str(comment.created)
            indent = 80 - len(info) - len(created)
            info = info + " "*indent + created + "\n"

            backmatter.append(info)
            backmatter.append("" + (80*"-") + "\n\n")
            for line in comment.text.splitlines():
                backmatter.append("{}\n".format(line))
            backmatter.append("\n")

        fp.write("".join(backmatter))
        fp.write('\n+++\n')
        fp.write(os.linesep)


def revisions(task):
    phid = utils.phid_lookup(task)
    t = model.Task(phid)
    for rev in t.revisions:
        print(rev.name, end=' ')
    print()

def rawdiff(diff_name):
    phid = utils.phid_lookup(diff_name)
    r = model.Revision(phid)

    commit_message = r.commitmessage

    print("From: {}  Mon Sep 17 00:00:00 2001".format(r.diff.base))
    print("From: {} <{}@{}>".format(r.diff.author.name, r.diff.author.username, utils.domain()))
    commitlines = commit_message.splitlines()
    print("Subject: [PATCH] {}".format(commitlines[0]))
    print("\n".join(commitlines[1:]))
    print()
    print("---")
    print()
    print(r.diff.rawdiff[:])

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
    update(task)

if cmd == "sync":
    sync(task)

if cmd == "create":
    create()

if cmd == "query":
    query()

if cmd == "diff":
    rawdiff(task)

if cmd == "diff-approve":
    diff_approve(task)

if cmd == "comments":
    comments()

if cmd == "revisions":
    revisions(task)

if cmd == "task":
    task = model.Task.fromName(task)
    transactions = task.comments
    for t in transactions:
        if t.author:
            pprint(t.author.name)
        print(t.comment)
        print()

if cmd == "project":
    utils.slug_lookup(task)

if cmd == "patch":
    # Use git apply --check to test if patch can be cleanly applied.
    phabdiff = "python3 {} diff {} test".format(str(spath) + "/phab.py", task)
    os.system("{} | git am --keep-non-patch -3".format(phabdiff))

