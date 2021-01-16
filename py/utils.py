import re
import os
from phabricator import Phabricator
from pprint import pprint
import frontmatter
import email
from frontmatter.default_handlers import YAMLHandler

phab = Phabricator()

def __init__():
    phab.update_interfaces()

def phid_lookup(name):
    result = phab.phid.lookup(names=[name])
    if(result):
        return result[name]['phid']
    return None

def slug_lookup(slug):
    result = phab.project.search(constraints={'slugs':[slug]})
    pprint(result)

def get_phid_transactions(phid):
    result = phab.transaction.search(objectIdentifier=phid, constraints={})
    return result['data']

def get_tasks(phids):
    if phids and len(phids) > 0:
        result = phab.maniphest.search(constraints={'phids':phids}, attachments={'projects': True})
        return result['data']
    return []

def get_users(phids):
    result = phab.user.search(constraints={'phids':phids})
    return result['data']

def get_username(username):
    result = phab.user.search(constraints={'usernames':[username]})
    return result['data'][0]

def get_revision(phid):
    result = phab.differential.revision.search(constraints={'phids':[phid]})
    return result['data'][0]

def approve_revision(phid):
        transactions=[]
        transactions.append({'type': 'accept', 'value': True})
        result = phab.differential.revision.edit(objectIdentifier=phid, transactions=transactions)
        pprint(result)

def get_diff(phid):
    result = phab.differential.diff.search(constraints={'phids':[phid]})
    return result['data'][0]

def get_rawdiff(id):
    result = phab.differential.getrawdiff(diffID=str(id))
    return result[:]

def get_commitmessage(revision_id):
    result = phab.differential.getcommitmessage(revision_id=revision_id)
    return result[:]

def task_get_revision_phids(phid):
    phids = []
    result = phab.edge.search(sourcePHIDs=[phid], types=["task.revision"])
    for item in result.data:
        phids.append(item['destinationPHID'])

    return phids

def task_get_mentions(phid):
    phids = []
    result = phab.edge.search(sourcePHIDs=[phid], types=["mention"])
    for item in result.data:
        phids.append(item['destinationPHID'])
    return phids

def task_create(title):
    return phab.maniphest.createtask(title=title)

def get_project(phid):
    result = phab.project.search(constraints={'phids': [phid]})
    return result['data'][0]

def transaction(type, value):
        return {'type': type, 'value': value}

def task_update(task, what):
    t = []
    if 'title' in what:
        t.append(transaction('title', task.title))
    if 'description' in what:
        t.append(transaction('description', task.description))
    if 'assigned' in what:
        t.append(transaction('owner', task.assigned.phid))
    if 'points' in what:
        t.append(transaction('points', task.points))
    if 'comment' in what:
        t.append(transaction('comment', task.comment))

    if(len(t) > 0):
        phab.maniphest.edit(objectIdentifier=task.phid, transactions=t)

def domain():
    return phab.user.whoami()['primaryEmail'].split('@')[1]

status_symbols = {
    'published': '🟣',
    'accepted':'🟢',
    'needs-review': '🟠',
    'draft': '🔵',
    'changes-planned': '🔴',
    'needs-revision': '🔨',
    'abandoned': '🛫',
}

def get_status_symbol(status):
    if(status in status_symbols):
        return status_symbols[status]

    return " "

def strike(text):
    result = ''
    for c in text:
        result = result + c + '\u0336'
    return result

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

def justify_strings(left, right, length):
    right=str(right)
    l = len(left)
    r = len(right)
    indent = length - l - r
    space = " "*indent
    return f"{left}{space}{right}"

def rfc2822(datetime):
    return email.utils.format_datetime(datetime)

def parse_matter(fp):
    post = frontmatter.load(fp)
    content = None
    backmatter = None

    if post.content.strip().endswith('+++'):
        content = post.content.rsplit("+++", 2)
        backmatter = content[1]
        content = content[0]
    else:
        content = post.content
        backmatter = None

    # Split new comment from backmatter
    comment = None
    if '::: Add Comment' in backmatter:
        comment = backmatter.split('::: Add Comment')
        comment = comment[-1].strip().splitlines()[1:]
        comment = "\n".join(comment).strip()


    return {
                'frontmatter': post.metadata,
                'content': content,
                'backmatter': backmatter,
                'comment': comment
        }
