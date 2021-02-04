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

    def diff_parsed(self, r, rawdiff):
        diff = ""
        uni = unidiff.PatchSet.from_string(rawdiff)
        for f in uni:
            source = ''
            target = ''
            # patch info is
            info = '' if f.patch_info is None else str(f.patch_info)
            if not f.is_binary_file and f:
                source = "--- %s%s\n" % (
                    f.source_file,
                    '\t' + f.source_timestamp if f.source_timestamp else '')
                target = "+++ %s%s\n" % (
                    f.target_file,
                    '\t' + f.target_timestamp if f.target_timestamp else '')
            diff += info + source + target

            for h in f:
                head = "@@ -%d,%d +%d,%d @@%s\n" % (
                    h.source_start, h.source_length,
                    h.target_start, h.target_length,
                    ' ' + h.section_header if h.section_header else '')

                diff += head

                for line in h:
                    if line.diff_line_no:
                        diff += str(line)

        template = self.templateEnv.get_template("rawdiff.diff")
        output = template.render(r=r, rawdiff=diff.strip(), utils=utils, show_comments=False, show_header=False, git=False)

        return output

    def genrawdiff(self, r, context, show_header=True):
        template = self.templateEnv.get_template("rawdiff.diff")


        if context:

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

            realpatch = template.render(r=r, rawdiff=self.diff_parsed(r, r.diff.diff), utils=utils, show_comments=False, show_header=False, git=False)
            if base_found:
                p = utils.run("git am --keep-non-patch -3", input=realpatch)
            else:
                # This is more complex, we need to apply the patch manually to out HEAD.
                print("Manually applying patch:")
                p = utils.run("git apply -3", input=realpatch)
                print(p.stderr)
                print(p.returncode)
                sys.exit(1)

            p = utils.run(f"git format-patch -U{context} --stdout HEAD~1")
            val = p.stdout

            os.chdir(cwd)
            utils.run(f"git worktree remove --force .git/phabrik/{r.diff.id}")
            p = utils.run(f"git tag -d phabrik/{r.diff.id}")

            output = template.render(r=r, rawdiff=val.strip(), utils=utils, show_comments=False, show_header=show_header, git=True)
        else:
            output = template.render(r=r, rawdiff=r.diff.diff, utils=utils, show_comments=False, show_header=show_header, git=False)

        return output.strip()

    def rawdiff(self, diff_name, context, show_comments):
        phid = utils.phid_lookup(diff_name)
        r = model.Revision.fromPHID(phid)

        if not show_comments:
            rawdiff = self.genrawdiff(r, context)
            print(self.diff_parsed(r, rawdiff))
            return 0

        rawdiff = self.genrawdiff(r, context, False)

        commentdiff = ""

        # Get revision inline comments, match them up with sources
        inlines = {}
        for i in r.inlines:
            if not i.path in inlines:
                inlines[i.path] = []
            inlines[i.path].append(i)

        uni = unidiff.PatchSet.from_string(rawdiff)

        for f in uni:
            if f.path in inlines:
                file_comments = {}
                source = ''
                target = ''
                # patch info is
                info = '' if f.patch_info is None else str(f.patch_info)
                if not f.is_binary_file and f:
                    source = "--- %s%s\n" % (
                        f.source_file,
                        '\t' + f.source_timestamp if f.source_timestamp else '')
                    target = "+++ %s%s\n" % (
                        f.target_file,
                        '\t' + f.target_timestamp if f.target_timestamp else '')
                commentdiff += info + source + target

                # We have an inline comment for this file!
                # Make a little dict so we can index them by line number easily!
                for i in inlines[f.path]:
                    if i.line not in file_comments:
                        file_comments[i.line] = []
                    file_comments[i.line].append(i)
                    #
                    # TODO
                    # Sort by line number and then by creationdata of comment.
                    #

                for h in f:
                    head = "@@ -%d,%d +%d,%d @@%s\n" % (
                        h.source_start, h.source_length,
                        h.target_start, h.target_length,
                        ' ' + h.section_header if h.section_header else '')

                    commentdiff += head

                    for l in h:
                        if l.is_added: commentdiff += '+'
                        if l.is_context: commentdiff += ' '
                        if l.is_removed: commentdiff += '-'
                        commentdiff = commentdiff + l.value
                        if l.target_line_no in file_comments:
                            for c in file_comments[l.target_line_no]:
                                commentdiff += f"#\n"
                                commentdiff += f"# {c.author.realName} ({c.author.username})::\n"
                                commentdiff += f"#---------------------------------------------------------\n"
                                lines = c.text.splitlines()
                                reflow = False
                                for line in lines:
                                    if len(line) > 120:
                                        reflow = True

                                if reflow:
                                    lines = textwrap.wrap(c.text, 80)

                                for line in lines:
                                    commentdiff += f"# {line}\n"
            else:
                source = ''
                target = ''
                # patch info is
                info = '' if f.patch_info is None else str(f.patch_info)
                if not f.is_binary_file and f:
                    source = "--- %s%s\n" % (
                        f.source_file,
                        '\t' + f.source_timestamp if f.source_timestamp else '')
                    target = "+++ %s%s\n" % (
                        f.target_file,
                        '\t' + f.target_timestamp if f.target_timestamp else '')
                commentdiff += info + source + target

                for h in f:
                    head = "@@ -%d,%d +%d,%d @@%s\n" % (
                        h.source_start, h.source_length,
                        h.target_start, h.target_length,
                        ' ' + h.section_header if h.section_header else '')

                    commentdiff += head

                    for line in h:
                        if line.diff_line_no:
                            commentdiff += str(line)

        template = self.templateEnv.get_template("rawdiff.diff")
        output = template.render(r=r, rawdiff=commentdiff.strip(), utils=utils, show_comments=True, show_header=True, git=False)
        print(output)



    def diff_comment(self, diff_name, context, show_comments):
        phid = utils.phid_lookup(diff_name)
        r = model.Revision.fromPHID(phid)
        rawdiff = self.genrawdiff(r, context)


        remove_comments = ""
        for line in sys.stdin.read().splitlines():
            if line.startswith('#'):
                continue
            remove_comments += line + "\n"

        annotated_diff = remove_comments
        matter = utils.parse_matter(annotated_diff)
        annotated_diff = matter['content'].strip()

        fd, path_orig = tempfile.mkstemp()
        with open(path_orig, 'w') as f:
            f.write(self.diff_parsed(r, rawdiff))
        os.close(fd)

        p = utils.run(f"diff -w -U0 {path_orig} -", input=self.diff_parsed(r, annotated_diff))

        os.unlink(path_orig)

        f = unidiff.PatchSet.from_string(p.stdout)
        if len(f) == 0:
            print("No inline-comments detected.")
        else:
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
            commentlines = 0
            bfirst = True
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
                c = {'dline': firstline.target_line_no-1, 'line': firstline.target_line_no-1-commentlines, 'v': text}
                commentlines = commentlines + len(text.splitlines())
                comments.append(c)
                #print(f"{c['dline']} : {c['line']} - {c['v'].strip()}")

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
                            if difflines == c['line'] or (difflines == total_diff_lines and c['line'] > total_diff_lines):
                                inline = {'path': p.path, 'line': l.target_line_no, 'comment': c['v']}
                                commentlines = commentlines + len(c['v'].splitlines())
                                inlines.append(inline)

            #
            # Finally we have a set of inlines, lets submit them.
            #
            #pprint(inlines)
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


