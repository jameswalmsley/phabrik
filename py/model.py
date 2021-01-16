import utils
from pprint import pprint
from pprint import pformat
from datetime import datetime

phid_cache = {}

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

    def __init__(self, raw):
        self.raw = raw
        self.author = User.fromPHID(raw['authorPHID'])
        self.text = raw['content']['raw']
        self.removed = raw['removed']
        self.created = datetime.fromtimestamp(raw['dateCreated'])
        self.modified = datetime.fromtimestamp(raw['dateModified'])

    @staticmethod
    def fromTransactions(ts):
        comments = []
        for t in ts:
            if t.type == 'comment':
                comments.append(Comment(t.raw['comments'][0]))
        return comments

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

class Project:
    phid = None
    raw = None
    slug = None
    name = None

    def __init__(self, phid):
        self.raw = utils.get_project(phid)
        r = self.raw
        self.phid = r['phid']
        self.slug = r['fields']['slug']
        self.name = r['fields']['name']
        phid_cache[self.phid] = self

    def __str__(self):
        return self.slug

    def __repr__(self):
        if self.slug:
            return self.slug
        else:
            return self.name

    @staticmethod
    def fromPHIDs(phids):
        projects = []
        for phid in phids:
            if phid in phid_cache:
                projects.append(phid_cache[phid])
            else:
                projects.append(Project(phid))
        return projects

class Diff:
    raw = None
    id = None
    phid = None
    __rawdiff = None
    base = None
    __author = None

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

class Revision:
    phid = None
    raw = None
    id = None
    name = None
    __diff = None
    __commitmessage = None
    __author = None
    diffPHID = None
    __transactions = None
    created = None

    def __init__(self, phid):
        self.raw = utils.get_revision(phid)
        r = self.raw
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
    def commitmessage(self):
        if not self.__commitmessage:
            self.__commitmessage = utils.get_commitmessage(self.id)
        return self.__commitmessage

    @property
    def author(self):
        if not self.__author:
            self.__author = User.fromPHID(self.raw['fields']['authorPHID'])
        return self.__author

    @staticmethod
    def fromPHIDs(phids):
        revs = []
        for phid in phids:
            revs.append(Revision(phid))
        return revs

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
            self.description = r['fields']['description']['raw']
            if self.points:
                self.points = int(self.points)
            self.title = self.name
            phid_cache[self.phid] = self

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

