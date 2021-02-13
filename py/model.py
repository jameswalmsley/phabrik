import utils
from pprint import pprint
from pprint import pformat
from datetime import datetime
import unidiff

phid_cache = {}

class Repo:
    raw = None
    phid = None
    staging = None

    def __init__(self, raw):
        self.raw = raw
        self.phid = raw['phid']
        if raw['staging']['supported']:
            self.staging = raw['staging']['uri']
        phid_cache[self.phid] = self

    @staticmethod
    def fromPHID(phid):
        if phid in phid_cache:
            return phid_cache[phid]
        raw = utils.get_repo(phid)
        return Repo(raw)

class User:
    raw = None
    realName = None
    username = None
    name = None
    phid = None
    def __init__(self, raw):
        if not raw:
            return
        self.raw = raw
        r = self.raw
        self.__dict__.update(r['fields'])
        self.phid = r['phid']
        self.name = self.realName
        phid_cache[self.phid] = self

    def __str__(self):
        return pformat(self.__dict__)

    @staticmethod
    def fromPHID(phid):
        if phid in phid_cache:
            return phid_cache[phid]
        raw = utils.get_users([phid])
        if(len(raw) > 0):
            return User(raw[0])

        user = User(None)
        user.phid = phid
        user.username = phid
        user.name = phid

        if "PHID-APPS" in phid:
            user.name = "Phabricator"
            user.username = "herald"

        return user

class Comment:
    phid = None
    author = None
    raw = None
    text = None
    removed = False
    created = None
    modified = None
    transacion = None

    def __init__(self, t):
        raw = t.raw['comments'][0]
        self.raw = raw
        self.author = User.fromPHID(raw['authorPHID'])
        self.text = raw['content']['raw']
        self.removed = raw['removed']
        self.created = datetime.fromtimestamp(raw['dateCreated'])
        self.modified = datetime.fromtimestamp(raw['dateModified'])
        self.transaction = t

    @staticmethod
    def fromTransactions(ts):
        comments = []
        for t in ts:
            if t.type == 'comment':
                comments.append(Comment(t))
        return comments

class InlineComment:
    phid = None
    author = None
    raw = None
    text = None
    done = None
    id = None
    transaction = None
    path = None
    line = None
    def __init__(self, t):
        self.transaction = t
        raw = t.raw
        self.raw = raw
        c = raw['comments'][0]
        self.author = User.fromPHID(raw['authorPHID'])
        self.text = c['content']['raw']
        self.id = c['id']
        self.phid = c['phid']
        self.path = raw['fields']['path']
        self.done = raw['fields']['isDone']
        self.line = raw['fields']['line']

    @staticmethod
    def fromTransactions(ts):
        inlines = []
        for t in ts:
            if t.type == 'inline':
                inlines.append(InlineComment(t))
        return inlines


class Transaction:
    phid = None
    raw = None
    type = None

    def __init__(self, raw):
        self.type = raw['type']
        self.phid = raw['phid']
        self.raw = raw

    @staticmethod
    def forPHID(phid):
        transactions = []
        trs = utils.get_phid_transactions(phid)
        for t in trs:
            transactions.append(Transaction(t))
        return transactions


class Diff:
    raw = None
    id = None
    phid = None
    base = None
    __author = None
    __rawdiff = None # Raw diff output from phabricator.
    __unidiff = None # Unidiff object of parsed raw diff.
    __diff = None # Ordered diff output from unidiff.

    def __init__(self, phid):
        self.raw = utils.get_diff(phid)
        r = self.raw
        self.phid = r['phid']
        self.id = r['id']
        for ref in r['fields']['refs']:
            if ref['type'] == 'base':
                self.base = ref['identifier']

        phid_cache[self.phid] = self

    @property
    def rawdiff(self):
        if not self.__rawdiff:
            self.__rawdiff = utils.get_rawdiff(self.id);
        return self.__rawdiff

    @property
    def author(self):
        if not self.__author:
            self.__author = User.fromPHID(self.raw['fields']['authorPHID'])
        return self.__author

    @property
    def unidiff(self):
        if not self.__unidiff:
            self.__unidiff = unidiff.PatchSet.from_string(self.rawdiff)
        return self.__unidiff

    @property
    def diff(self):
        if not self.__diff:
            self.__diff = ""
            for patch in reversed(self.unidiff):
                self.__diff += str(patch)

        return self.__diff


class Revision:
    phid = None
    raw = None
    id = None
    name = None
    __diff = None
    __repo = None
    __commitmessage = None
    __author = None
    diffPHID = None
    __transactions = None
    __comments = None
    __inlines = None
    comment = None
    created = None

    def __init__(self, r):
        self.raw = r
        self.phid = r['phid']
        self.id = r['id']
        self.name = "D{}".format(self.id)
        self.__dict__.update(r['fields'])
        self.closed = self.status['closed']
        self.status = self.status['value']
        self.created = datetime.fromtimestamp(self.dateCreated)
        phid_cache[self.phid] = self

    @property
    def diff(self):
        if not self.__diff:
            self.__diff = Diff(self.diffPHID)
        return self.__diff

    @property
    def repo(self):
        if not self.__repo:
            self.__repo = Repo.fromPHID(self.repositoryPHID)
        return self.__repo

    @property
    def commitmessage(self):
        if not self.__commitmessage:
            self.__commitmessage = utils.get_commitmessage(self.id).strip()
        return self.__commitmessage

    @property
    def author(self):
        if not self.__author:
            self.__author = User.fromPHID(self.raw['fields']['authorPHID'])
        return self.__author

    @staticmethod
    def fromPHID(phid):
        raw = utils.get_revision(phid)
        return Revision(raw)

    @staticmethod
    def fromPHIDs(phids):
        revs = []
        for phid in phids:
            revs.append(Revision.fromPHID(phid))
        return revs

    @staticmethod
    def querySubscribed(userphid):
        revs = []
        raw = utils.query_subscribed_revisions(userphid)
        for r in raw:
            revs.append(Revision(r))
        return revs

    @property
    def transactions(self):
        if not self.__transactions:
            self.__transactions = Transaction.forPHID(self.phid)
        return self.__transactions

    @property
    def comments(self):
        if not self.__comments:
            self.__comments = Comment.fromTransactions(self.transactions)
        return self.__comments

    @property
    def inlines(self):
        if not self.__inlines:
            self.__inlines = InlineComment.fromTransactions(self.transactions)
        return self.__inlines

    def __str__(self):
        return pformat(self.__dict__)

class Task(object):
    raw = None
    id = None
    description = None
    authorPHID = None
    ownerPHID = None
    phid = None
    points = None
    title = None
    priority = None
    __columns = None

    __project_phids = None
    __projects = None
    __attached_project_phids = None
    tags = []

    __author = None
    __assigned = None
    __revision_phids = None
    __revisions = None

    __transactions = None
    __comments = None

    comment = None

    def __init__(self, raw):
        if(raw):
            self.raw = raw
            r = self.raw
            self.id = r['id']
            self.phid = r['phid']
            self.__dict__.update(r['fields'])
            self.description = r['fields']['description']['raw'].strip()
            if self.points:
                self.points = float(self.points)
            self.title = self.name
            self.__columns = {}
            if 'columns' in r['attachments']:
                for i, (k,v) in enumerate(r['attachments']['columns']['boards'].items()):
                    self.__columns[k] = v

            phid_cache[self.phid] = self

    def getColumn(self, projphid):
        if projphid in self.__columns:
            return self.__columns[projphid]
        return None

    @staticmethod
    def fromPHIDs(phids):
        tasks = []
        raw = utils.get_tasks(phids)
        for r in raw:
            tasks.append(Task(r))
        return tasks

    @staticmethod
    def fromPHID(phid):
        t = Task.fromPHIDs([phid])
        if len(t) == 1:
            return t[0]
        return None

    @staticmethod
    def fromName(name):
        phid = utils.phid_lookup(name)
        return Task.fromPHID(phid)

    @staticmethod
    def queryAssigned(userphid):
        raw = utils.get_assigned_tasks(userphid);
        tasks = []
        for r in raw:
            tasks.append(Task(r))
        return tasks

    @staticmethod
    def queryProjectTasks(phid):
        raws = utils.get_project_tasks(phid)
        tasks = []
        for r in raws:
            tasks.append(Task(r))
        return tasks

    @property
    def assigned(self):
        if not self.__assigned and self.ownerPHID:
            self.__assigned = User.fromPHID(self.ownerPHID)
        return self.__assigned

    @assigned.setter
    def assigned(self, username):
        raw = utils.get_username(username)
        self.ownerPHID = raw['phid']

    @property
    def author(self):
        if not self.__author and self.authorPHID:
            self.__author = User.fromPHID(self.authorPHID)
        return self.__author

    @property
    def transactions(self):
        if not self.__transactions:
            self.__transactions = Transaction.forPHID(self.phid)
        return self.__transactions

    @property
    def comments(self):
        if not self.__comments:
            self.__comments = Comment.fromTransactions(self.transactions)
        return self.__comments

    @property
    def revision_phids(self):
        if not self.__revision_phids:
            self.__revision_phids = [] + utils.task_get_revision_phids(self.phid)
        return self.__revision_phids

    @property
    def revisions(self):
        if not self.__revisions:
            self.__revisions = Revision.fromPHIDs(self.revision_phids)
        return self.__revisions

    @property
    def project_phids(self):
        if not self.__project_phids:
            self.__project_phids = [] + self.raw['attachments']['projects']['projectPHIDs']
        return self.__project_phids

    @property
    def projects(self):
        if not self.__projects:
            self.__projects = Project.fromPHIDs(self.project_phids)
        return self.__projects

    def commit(self):
        what = {}
        if(self.description):
            what['description'] = True
        if(self.title):
            what['title'] = True
        if(self.points):
            what['points'] = True
        if(self.assigned):
            what['assigned'] = True
        if(self.__attached_project_phids):
            what['attach-projects'] = True
        if(self.comment):
            what['comment'] = True

        utils.task_update(self, what)

class Column:
    phid = None
    raw = None
    name = None
    id = None
    tasks = None
    def __init__(self, r):
        self.tasks = []
        self.raw = r
        self.phid = r['phid']
        self.id = r['id']
        self.__dict__.update(r['fields'])
        phid_cache[self.phid] = self

    @staticmethod
    def queryProject(phid):
        cols = []
        raws = utils.get_project_columns(phid)
        for r in raws:
            cols.append(Column(r))

        return cols

class Project:
    phid = None
    raw = None
    name = None
    id = None
    color = None
    created = None
    modified = None
    depth = None
    description = None
    icon = None
    milestone = None
    parent = None
    slug = None
    subtype = None

    __columns = None
    __coldict = None
    __tasks = None

    def __init__(self, r):
        self.raw = r
        self.phid = r['phid']
        self.id = r['id']
        self.__dict__.update(r['fields'])
        phid_cache[self.phid] = self

    @property
    def columns(self):
        if not self.__columns:
            self.__columns = Column.queryProject(self.phid)
            self.__coldict = {}
            for c in self.__columns:
                self.__coldict[c.phid] = c

            for t in self.tasks:
                col = t.getColumn(self.phid)
                if col:
                    colphid = col['columns'][0]['phid']
                    self.__coldict[colphid].tasks.append(t)
        return self.__columns

    @property
    def tasks(self):
        if not self.__tasks:
            self.__tasks = Task.queryProjectTasks(self.phid)

        return self.__tasks

    @staticmethod
    def fromMany(raws):
        projs = []
        for r in raws:
            if r['phid'] in phid_cache:
                projs.append(phid_cache[r['phid']])
            else:
                projs.append(Project(r))

        return projs

    @staticmethod
    def queryUserProjects(phid):
        return Project.fromMany(utils.get_user_projects(phid))

    def __str__(self):
        return self.slug

    def __repr__(self):
        if self.slug:
            return self.slug
        else:
            return self.name

    @staticmethod
    def fromPHID(phid):
        if phid in phid_cache:
            return phid_cache[phid]
        else:
            return Project(utils.get_project(phid))

    @staticmethod
    def fromPHIDs(phids):
        projects = []
        for phid in phids:
            projects.append(Project.fromPHID(phid))
        return projects

    @staticmethod
    def fromID(id):
        return Project(utils.get_project_id(id))
