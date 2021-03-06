import unidiff
import os
import tempfile
import utils
import textwrap

from pprint import pprint

class ParsedDiff(object):
    rawdiff = None
    unidiff = None

    def __init__(self, rawdiff):
        stripped = ""
        keep=False
        for i, l in enumerate(rawdiff.splitlines()):
            if l.startswith('diff'):
                keep=True
            if keep:
                if l.startswith('#'):
                    continue
                stripped += l + '\n'

        self.rawdiff = stripped
        self.unidiff = unidiff.PatchSet.from_string(self.rawdiff)

    def parsed(self, annotate=False, revision=None):
        r=revision
        # Get revision inline comments, match them up with sources
        inlines = {}
        if annotate and revision:
            for i in r.inlines:
                if not i.path in inlines:
                    inlines[i.path] = []
                inlines[i.path].append(i)

        uni = self.unidiff

        commentdiff = ""

        for f in uni:
            has_inlines = f.path in inlines
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

            if has_inlines:
                # We have an inline comment for this file!
                # Make a little dict so we can index them by line number easily!
                for i in inlines[f.path]:
                    if i.line not in file_comments:
                        file_comments[i.line] = []
                    file_comments[i.line].insert(0, i)

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
                    if has_inlines and l.target_line_no in file_comments:
                        for c in file_comments[l.target_line_no]:
                            commentdiff += f"#\n"
                            commentdiff += f"# {c.author.realName} ({c.author.username})::\n"
                            commentdiff += f"#---------------------------------------------------------\n"
                            lines = c.text.splitlines()
                            lines = textwrap.wrap(c.text, 80) #mdformat.text(c.text, options="wrap").splitlines()

                            for line in lines:
                                commentdiff += f"# {line}\n"

        return commentdiff

    def comments(self, annotated):
        fd, temp_path = tempfile.mkstemp()
        with open(temp_path, 'w') as f:
            f.write(self.parsed())
        os.close(fd)

        raw_annotated = ""
        keep = False
        for l in annotated.splitlines():
            if l.startswith('diff'):
                keep = True
            if not keep:
                continue
            if l.startswith('#'):
                continue
            if l == '--':
                break
            raw_annotated += l + '\n'

        p = utils.run(f"diff -w -U0 {temp_path} -", input=raw_annotated)

        ps = unidiff.PatchSet.from_string(p.stdout)
        if len(ps) == 0:
            return []

        f = ps[0]

        comments = []
        commentlines = 0

        for comment in f:
            text = ""
            firstline = None
            for line in comment:
                if line.is_added:
                    text += line.value
                    if not firstline: firstline = line

            if firstline is None:
                continue

            if len(text.strip()) > 0:
                c = {'dline': firstline.target_line_no-1, 'line': firstline.target_line_no-1-commentlines, 'v': text}
                commentlines += len(text.splitlines())
                comments.append(c)

        return comments

    def inlines(self, comments):
        #
        # iterate through the main diff, and match comments with their source files.
        #
        total_diff_lines = len(self.parsed().splitlines())
        inlines = []
        difflines = 0
        commentlines = 0
        for p in self.unidiff:
            for h in p:
                for l in h:
                    if not l.diff_line_no:
                        break;
                    if l.diff_line_no > difflines:
                        difflines = l.diff_line_no

                    for c in comments:
                        if difflines == c['line'] or (difflines == total_diff_lines and c['line'] > total_diff_lines):
                            newfile = True
                            line = l.target_line_no
                            if(l.is_removed):
                                newfile = False
                                line = l.source_line_no

                            inline = {'path': p.path, 'line': line, 'comment': c['v'], 'newfile': newfile}
                            commentlines += len(c['v'].splitlines())
                            inlines.append(inline)
        return inlines

    def annotate(self, r):
        return self.parsed(annotate=True, revision=r)
