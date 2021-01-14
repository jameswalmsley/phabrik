import utils
import pprint

class User:
    raw = None
    username = None
    name = None
    phid = None
    def __init__(self, phid):
        self.raw = utils.get_user(phid)
        r = self.raw
        self.__dict__.update(r['fields'])
        self.phid = r['phid']
        self.name = self.realName

    def __str__(self):
        return pprint.pformat(self.__dict__)

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

    @property
    def rawdiff(self):
        if not self.__rawdiff:
            self.__rawdiff = utils.get_rawdiff(self.id);
        return self.__rawdiff

    @property
    def author(self):
        if not self.__author:
            self.__author = User(self.raw['fields']['authorPHID'])
        return self.__author

class Revision:
    raw = None
    id = None
    name = None
    __diff = None
    __commitmessage = None
    __author = None
    diffPHID = None

    def __init__(self, phid):
        self.raw = utils.get_revision(phid)
        r = self.raw
        self.id = r['id']
        self.name = "D{}".format(self.id)
        self.__dict__.update(r['fields'])
        self.closed = self.status['closed']
        self.status = self.status['value']

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
            self.__author = User(r['fields']['authorPHID'])
        return self.__author

    @staticmethod
    def fromPHIDs(phids):
        revs = []
        for phid in phids:
            revs.append(Revision(phid))
        return revs

    def __str__(self):
        return pprint.pformat(self.__dict__)

class Task:
    raw = None
    id = None
    description = None
    authorPHID = None
    ownerPHID = None
    phid = None
    points = None
    title = None

    __author = None
    __assigned = None
    __revision_phids = None
    __revisions = None

    def __init__(self, phid):
        if(phid):
            self.raw = utils.get_task(phid)
            r = self.raw
            self.id = r['id']
            self.phid = r['phid']
            self.__dict__.update(r['fields'])
            self.description = r['fields']['description']['raw']

    @property
    def assigned(self):
        if not self.__assigned and self.ownerPHID:
            self.__assigned = User(self.ownerPHID)
        return self.__assigned

    @assigned.setter
    def assigned(self, username):
        raw = utils.get_username(username)
        self.ownerPHID = raw['phid']

    @property
    def author(self):
        if not self.__author and self.authorPHID:
            self.__author = User(self.authorPHID)
        return self.__author


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

        utils.task_update(self, what)

