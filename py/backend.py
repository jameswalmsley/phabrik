import sys
import os
from frontmatter.default_handlers import YAMLHandler
import utils
import diff
import model
import frontmatter
import tempfile
from pprint import pprint
from io import BytesIO, SEEK_SET
import jinja2
import unidiff
import textwrap

class Backend(object):
    def __init__(self, spath):
        self.templateLoader = jinja2.FileSystemLoader(searchpath=spath+"/templates")
        self.templateEnv = jinja2.Environment(loader=self.templateLoader, trim_blocks=True, lstrip_blocks=True)

    def task_update(self, task):
        description=""

        matter = utils.parse_matter(sys.stdin.read())
        post = matter['frontmatter']
        description = matter['content'].strip()

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

    def task(self,task):
        t = model.Task.fromName(task)

        template = self.templateEnv.get_template("task.md")

        post = None
        post = frontmatter.Post("")
        post.content = t.description
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
                    tags.append(proj.slug)
                else:
                    projects.append(proj.name)
            post['tags'] = tags
            post['projects'] = projects

        if t.title:
            post['title'] = t.title

        yh = YAMLHandler()
        fm = yh.export(post.metadata)

        output = template.render(frontmatter=fm, description=post.content.strip(), task=t, utils=utils)
        print(output)

    def context(self, r, parsed, context):
        p = utils.run("git rev-parse HEAD")
        base_sha = p.stdout
        base_found = False

        p = utils.run(f"git show --stat {r.diff.base}")
        if(p.returncode == 0):
            base_sha = r.diff.base
            base_found = True
        else:
            p = utils.run(f"git fetch -n {r.repo.staging} refs/tags/phabricator/base/{r.diff.id}:refs/tags/phabrik/{r.diff.id}")
            if(p.returncode == 0):
                base_sha = f"phabrik/{r.diff.id}"
                base_found = True

        p = utils.run(f"git worktree add --detach --no-checkout .git/phabrik/{r.diff.id} {base_sha}")

        cwd = os.getcwd()
        os.chdir(f".git/phabrik/{r.diff.id}")

        utils.run("git reset")

        realpatch = self.genpatch(r, parsed.parsed(), False, False, True)
        if base_found:
            p = utils.run("git am --keep-non-patch -3", input=realpatch)
        else:
            # This is more complex, we need to apply the patch manually to our HEAD.
            p = utils.run("git apply -3", input=realpatch)

        p = utils.run(f"git format-patch -U{context} --stdout HEAD~1", input=realpatch)
        val = p.stdout

        os.chdir(cwd)
        utils.run(f"git worktree remove --force .git/phabrik/{r.diff.id}")
        p = utils.run(f"git tag -d phabrik/{r.diff.id}")

        return diff.ParsedDiff(val)

    def genpatch(self, r, rawdiff, comments, git, header):
        template = self.templateEnv.get_template("rawdiff.diff")
        output = template.render(r=r, rawdiff=rawdiff, utils=utils, show_comments=comments, show_header=header, git=git)
        return output

    def rawdiff(self, diff_name, context, show_comments):
        phid = utils.phid_lookup(diff_name)
        r = model.Revision.fromPHID(phid)
        rawdiff = diff.ParsedDiff(str(r.diff.diff))
        if context:
            rawdiff = self.context(r, rawdiff, context)

        if not show_comments:
            patch = self.genpatch(r, rawdiff.parsed(), False, False, True)
            print(patch, end='')
            return 0

        annotated = rawdiff.annotate(r)
        print(self.genpatch(r, annotated, True, False, True), end='')
        return 0


    def diff_comment(self, diff_name, context, show_comments):
        phid = utils.phid_lookup(diff_name)
        r = model.Revision.fromPHID(phid)

        annotated_diff = sys.stdin.read()

        matter = utils.parse_matter(annotated_diff)
        annotated_diff = matter['content']

        d = diff.ParsedDiff(str(r.diff.diff))

        if context:
            d = self.context(r, d, context)

        comments = d.comments(annotated_diff)

        inlines = d.inlines(comments)

        utils.diff_inline_comments(phid, r.id, inlines)

        # Do we have normal comments?
        if len(matter['comment']):
            utils.diff_add_comment(phid, matter['comment'])


    def create(self, title):
        tid = utils.task_create(title)
        print("T{}".format(tid['id'].strip()))

    def dashboard(self):
        whoami = utils.whoami()
        tasks = model.Task.queryAssigned(whoami)
        revs = model.Revision.querySubscribed(whoami)
        projects = model.Project.queryUserProjects(whoami)

        rd = {}
        for r in revs:
            if r.status in rd:
                rd[r.status].append(r)
            else:
                rd[r.status] = [r]

        template = self.templateEnv.get_template("dashboard.md")

        output = template.render(utils=utils, assigned=tasks, responsible=rd, projects=projects)
        print(output)
        return 0

    def diff_plan_changes(self, diff_name):
        phid = utils.phid_lookup(diff_name)
        utils.diff_action(phid, 'plan-changes')

    def diff_request_review(self, diff_name):
        phid = utils.phid_lookup(diff_name)
        utils.diff_action(phid, 'request-review')

    def diff_close(self, diff_name):
        phid = utils.phid_lookup(diff_name)
        utils.diff_action(phid, 'close')

    def diff_reopen(self, diff_name):
        phid = utils.phid_lookup(diff_name)
        utils.diff_action(phid, 'reopen')

    def diff_abandon(self, diff_name):
        phid = utils.phid_lookup(diff_name)
        utils.diff_action(phid, 'abandon')

    def diff_accept(self, diff_name):
        phid = utils.phid_lookup(diff_name)
        utils.diff_action(phid, 'accept')

    def diff_reclaim(self, diff_name):
        phid = utils.phid_lookup(diff_name)
        utils.diff_action(phid, 'reclaim')

    def diff_request_changes(self, diff_name):
        phid = utils.phid_lookup(diff_name)
        utils.diff_action(phid, 'reject')

    def diff_commandeer(self, diff_name):
        phid = utils.phid_lookup(diff_name)
        utils.diff_action(phid, 'commandeer')

    def diff_resign(self, diff_name):
        phid = utils.phid_lookup(diff_name)
        utils.diff_action(phid, 'resign')

    def projects(self):
        phid = utils.whoami()
        projs = model.Project.queryUserProjects(phid)
        for p in projs:
            print("{} - {}".format(p.name, p.phid))

    def project(self, id):
        proj = model.Project.fromID(int(id[1:]))
        template = self.templateEnv.get_template("workboard.md")

        output = template.render(utils=utils, project=proj)
        print(output)

