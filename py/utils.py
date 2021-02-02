import os
from phabricator import Phabricator
from pprint import pprint
import frontmatter
import email
from frontmatter.default_handlers import YAMLHandler
import subprocess
import pathlib

phab = Phabricator()
spath = None

def __init__(path):
    global spath
    phab.update_interfaces()
    spath = path

def phab_host():
    return str(pathlib.Path(phab.host).parent)

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

def get_assigned_tasks(user_phid):
    result = phab.maniphest.search(constraints={'assigned': [user_phid], 'statuses': ['open']}, attachments={'projects': True})
    return result['data']

def get_users(phids):
    result = phab.user.search(constraints={'phids':phids})
    return result['data']

def get_username(username):
    result = phab.user.search(constraints={'usernames':[username]})
    return result['data'][0]

def get_user_projects(userphid):
    result = phab.project.search(constraints={'members':[userphid]}, queryKey='active')
    return result['data']

def get_project_tasks(phid):
    result = phab.maniphest.search(constraints={'projects':[phid], 'statuses':['open']}, attachments={'columns': True})
    return result['data']

def get_project_columns(phid):
    result = phab.project.column.search(constraints={'projects': [phid]})
    return result['data']

def whoami():
    return phab.user.whoami()['phid']

def get_revision(phid):
    result = phab.differential.revision.search(constraints={'phids':[phid]})
    return result['data'][0]

def query_subscribed_revisions(userphid):
    result = phab.differential.revision.search(constraints={'responsiblePHIDs': [userphid], 'statuses': ['open', 'accepted', 'needs-review', 'draft', 'changes-planned', 'needs-revision']})
    return result['data']

def get_diff(phid):
    result = phab.differential.diff.search(constraints={'phids':[phid]})
    return result['data'][0]

def get_rawdiff(id):
    result = phab.differential.getrawdiff(diffID=str(id))

    #
    # The rawdiff result from the API always appends 2 '\n'
    # Characters.
    #
    # Whitespaces in diff's are important so lets remove the problem
    # here.
    #
    return result[:-2]

def get_commitmessage(revision_id):
    result = phab.differential.getcommitmessage(revision_id=revision_id)
    return result[:]

def diff_action(phid, action):
    transactions = []
    transactions.append({'type': action, 'value': True})
    phab.differential.revision.edit(objectIdentifier=phid, transactions=transactions)

def diff_add_comment(phid, comment):
    transactions = []
    transactions.append({'type': 'comment', 'value': comment})
    phab.differential.revision.edit(objectIdentifier=phid, transactions=transactions)


def diff_inline_comments(phid, id, inlines):
    for i in inlines:
        phab.differential.createinline(revisionID=id, filePath=i['path'], isNewFile=True, lineNumber=i['line'], content=i['comment'])

    p = run(f"bash {spath}/diffget.sh {phab_host()} {id}")
    tags = p.stdout.split('<')
    for t in tags:
        if 'csrf' in t:
            for x in t.split(' '):
                if 'value' in x:
                    token  = x.split('"')[1].split('"')[0]
                    os.system(f"bash {spath}/submit.sh {phab_host()} {id} {token}")

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

def get_project_id(id):
    result = phab.project.search(constraints={'ids': [id]})
    return result['data'][0]

def get_repo(phid):
    result = phab.repository.query(phids=[phid])
    return result[0]

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

diff_status_symbols = {
    'published': '🟣',
    'accepted':'🟢',
    'needs-review': '🟠',
    'draft': '🔵',
    'changes-planned': '🔴',
    'needs-revision': '🔨',
    'abandoned': '🛫',
}

def get_diff_status_symbol(status):
    if(status in diff_status_symbols):
        return diff_status_symbols[status]

    return " "

priority_color_symbols = {
    'pink': ' ',
    'violet': '🟣',
    'red': '🔴',
    'orange': '🟠',
    'yellow': ' ',
    'sky': ' ',
}

priority2color = {
    'Unbreak Now': 'pink',
    'Needs Triage': 'violet',
    'High': 'red',
    'Normal': 'orange',
    'Low': 'yellow',
    'Wishlist': 'sky'
}

def get_priority_symbol(priority):
    if priority in priority2color:
        color = priority2color[priority]
        if(color in priority_color_symbols):
            return priority_color_symbols[color]
    return " "

def strike(text):
    result = ''
    for c in text:
        result = result + c + '\u0336'
    return result

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
    if backmatter and '::: Add Comment' in backmatter:
        comment = backmatter.split('::: Add Comment')
        comment = comment[-1].strip().splitlines()[1:]
        comment = "\n".join(comment).strip()

    if not comment:
        comment = []

    return {
                'frontmatter': post.metadata,
                'content': content,
                'backmatter': backmatter,
                'comment': comment
        }


def system(cmd):
    fd = os.popen(cmd)
    out = fd.read()
    ret = fd.close()
    if ret == None:
        ret = 0
    return (ret, out)

def run(cmd, input=None):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, input=input, encoding="utf-8", shell=True)
    return p
