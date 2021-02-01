import sys
import os
from frontmatter.default_handlers import YAMLHandler
import utils
import model
import frontmatter
import tempfile
from pprint import pprint
from io import BytesIO, SEEK_SET
import jinja2
import unidiff

class Backend(object):
    def __init__(self, spath):
        self.templateLoader = jinja2.FileSystemLoader(searchpath=spath+"/templates")
        self.templateEnv = jinja2.Environment(loader=self.templateLoader)

    def task_update(self, task):
        description=""

        matter = utils.parse_matter(sys.stdin)
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

    def genrawdiff(self, r, context, show_comments):
        template = self.templateEnv.get_template("rawdiff.diff")


        if context != None:

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

            realpatch = template.render(r=r, utils=utils, show_comments=false)
            if base_found:
                p = utils.run("git am --keep-non-patch -3", input=realpatch)
            else:
                # This is more complex, we need to apply the patch manually to out HEAD.
                print("Manually applying patch:")
                p = utils.run("git apply -3", input=output)
                print(p.stderr)
                print(p.returncode)
                sys.exit(1)

            p = utils.run(f"git format-patch -U{context} --stdout HEAD~1")
            val = p.stdout

            os.chdir(cwd)
            utils.run(f"git worktree remove --force .git/phabrik/{r.diff.id}")
            p = utils.run(f"git tag -d phabrik/{r.diff.id}")

            return val.strip()

        output = template.render(r=r, utils=utils, show_comments=show_comments)

        return output

    def rawdiff(self, diff_name, context, show_comments):
        phid = utils.phid_lookup(diff_name)
        r = model.Revision.fromPHID(phid)
        print(self.genrawdiff(r, context, show_comments))

    def diff_comment(self, diff_name, context, show_comments):
        phid = utils.phid_lookup(diff_name)
        r = model.Revision.fromPHID(phid)
        rawdiff = self.genrawdiff(r, context, False)

        annotated_diff = sys.stdin.read()

        fd, path_orig = tempfile.mkstemp()
        with open(path_orig, 'w') as f:
            f.write(rawdiff)
        os.close(fd)

        p = utils.run(f"diff -w -U0 {path_orig} -", input=annotated_diff)

        os.unlink(path_orig)

        f = unidiff.PatchSet.from_string(p.stdout)
        if len(f) == 0:
            print("No comments detected.")
            return -1
        f = f[0]
        uni = unidiff.PatchSet.from_string(rawdiff)
        total_diff_lines = 0

        #
        # Find out what unidiff has parsed the last diff line to be.
        # This allows us to attach any comments on the end to the last line.
        #
        for p in uni:
            for h in p:
                for l in h:
                    if l.diff_line_no:
                        total_diff_lines = l.diff_line_no

        #
        # Extract the additions from the diffs! Each hunk is an in-line comment.
        #
        comments = []
        for comment in f:
            text = ""
            # Capture the firstline number of the hunk.
            # The targetline before the start of the new hunk is where the comment
            # was placed.
            firstline = None
            for line in comment:
                # Only additions can be comments.
                if line.is_added:
                    # Get all the lines of the hunk as a block-comment.
                    text = text + line.value
                    if firstline is None:
                        firstline = line
            # Mini object to describe this comment,
            c = {'dline': firstline.target_line_no-1, 'line': firstline.source_line_no, 'v': text}
            comments.append(c)

        #
        # Iterate through the main diff, and match comments to original source files.
        #
        inlines = []
        difflines = 0
        commentlines = 0
        for p in uni:
            for h in p:
                for l in h:
                    if not l.diff_line_no:
                        break
                    if(l.diff_line_no and l.diff_line_no > difflines):
                        difflines = l.diff_line_no

                    for c in comments:
                        if difflines == c['dline'] or (difflines == total_diff_lines and c['dline'] > total_diff_lines):
                            inline = {'path': p.path, 'line': l.target_line_no-commentlines, 'comment': c['v']}
                            commentlines = commentlines + len(c['v'].splitlines())
                            inlines.append(inline)

        #
        # Finally we have a set of inlines, lets submit them.
        #
        utils.diff_inline_comments(phid, r.id, inlines)


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


