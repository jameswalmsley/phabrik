import os
import utils
import model
import frontmatter
from pprint import pprint
from io import BytesIO, SEEK_SET

class Backend(object):
    def __init__(self):
        return

    def update(self, task, file):
        description=""

        with open(file, 'r') as fp:
            matter = utils.parse_matter(fp)
            post = matter['frontmatter']
            description = utils.vimwiki2phab(matter['content'])

            t = model.Task(None)
            t.phid = utils.phid_lookup(task)
            t.description = description

            if('title' in post):
                    t.title = post['title']
            if('points' in post):
                    t.points = post['points']
            if('assigned' in post):
                    t.assigned = post['assigned']

            if len(matter['comment']):
                    t.comment = matter['comment']

            t.commit()



    def sync(self,task, file):
        t = model.Task.fromName(task)

        post = None
        with open(file, 'r') as fp:
            post = frontmatter.load(fp)

        with open(file, 'w+') as fp:
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

            fp.write('+++\n\n')

            fp.write("-"*80+"\n\n")

            backmatter = []
            for rev in t.revisions:
                status = utils.get_status_symbol(rev.status)
                title = rev.title
                if(rev.closed):
                    title = utils.strike(title)
                backmatter.append("{} - {} - {}\n".format(rev.name, status, title))

            backmatter.append("\n")
            backmatter.append("-"*80+"\n\n")

            backmatter.append("Comments:\n")
            backmatter.append("" + (80*"=") + "\n\n")

            for comment in t.comments:
                if comment.removed:
                    continue
                info = "{} ({}):".format(comment.author.name, comment.author.username)
                created = "`{}`".format(str(comment.created))
                indent = 80 - len(info) - len(created)
                info = info + " "*indent + created + "\n"

                backmatter.append(info)
                backmatter.append("" + (80*"-") + "\n\n")
                for line in comment.text.splitlines():
                    backmatter.append("{}\n".format(line))
                backmatter.append("\n")

            backmatter.append("::: Add Comment\n")
            backmatter.append("-"*80+"\n\n")

            fp.write("".join(backmatter))
            fp.write('\n+++\n\n')

    def rawdiff(self, diff_name):
        phid = utils.phid_lookup(diff_name)
        r = model.Revision(phid)

        commit_message = r.commitmessage

        print("From: {}  Mon Sep 17 00:00:00 2001".format(r.diff.base))
        print("From: {} <{}@{}>".format(r.author.name, r.author.username, utils.domain()))
        commitlines = commit_message.splitlines()
        print("Subject: [PATCH] {}".format(commitlines[0]))
        print("\n".join(commitlines[1:]))
        print()
        print("---")
        print()
        print(r.diff.rawdiff[:])

    def create(self, title):
        tid = utils.task_create(title)
        print('T'+tid['id']+'.md')

    def approve_revision(self, diff_name):
        phid = utils.phid_lookup(diff_name)
        utils.approve_revision(phid)
