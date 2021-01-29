import os
import sys
import pathlib
import argparse

import utils
import backend

spath = pathlib.Path(__file__).parent.absolute()

utils.__init__(spath)
backend = backend.Backend(str(spath))

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="subcommand")

def subcommand(args=[], parent=subparsers):
    """Decorator to add to functions.
    See https://mike.depalatis.net/blog/simplifying-argparse.html
    """
    def decorator(func):
        parser = parent.add_parser(func.__name__, description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)
    return decorator

def argument(*name_or_flags, **kwargs):
    """Helper function to satisfy argparse.ArgumentParser.add_argument()'s
    input argument syntax"""
    return (list(name_or_flags), kwargs)


def main():
    # Try to obtain version
    __version__ = '0.0.0'

    parser.add_argument('-v', '--version', action='version', version=__version__)

    args = parser.parse_args()
    if args.subcommand is None:
        parser.print_help()
    else:
        return args.func(args)

@subcommand([argument('task', help="Task number e.g. T123"),
             argument('source', help="Task source file")])
def update(args):
    backend.update(args.task, args.source)
    backend.sync(args.task, args.source)

@subcommand([argument('task', help="Task number e.g. T123"),
             argument('--update', help="Parse stdin and update task", action='store_true')])
def task(args):
    if(args.update):
        return backend.task_update(args.task)

    backend.task(args.task)

@subcommand([])
def dashboard(args):
    backend.dashboard()

@subcommand([argument('title')])
def create(args):
    backend.create(args.title)

@subcommand([argument('diff'),
             argument('--comment', action="store_true"),
             argument('--context', dest="context"),
             argument('--plan-changes', action="store_true"),
             argument('--request-review', action="store_true"),
             argument('--close', action="store_true"),
             argument('--reopen', action="store_true"),
             argument('--abandon', action="store_true"),
             argument('--approve', action="store_true"),
             argument('--reclaim', action="store_true"),
             argument('--request-changes', action="store_true"),
             argument('--commandeer', action="store_true"),
             argument('--resign', action="store_true"),
])
def diff(args):
    if(args.plan_changes):
        return backend.diff_plan_changes(args.diff)
    if(args.request_review):
        return backend.diff_request_review(args.diff)
    if(args.close):
        return backend.diff_close(args.diff)
    if(args.reopen):
        return backend.diff_reopen(args.diff)
    if(args.abandon):
        return backend.diff_abandon(args.diff)
    if(args.approve):
        return backend.diff_accept(args.diff)
    if(args.reclaim):
        return backend.diff_reclaim(args.diff)
    if(args.request_changes):
        return backend.diff_request_changes(args.diff)
    if(args.commandeer):
        return backend.diff_commandeer(args.diff)
    if(args.resign):
        return backend.diff_resign(args.diff)

    if(args.comment):
        return backend.diff_comment(args.diff, args.context)

    return backend.rawdiff(args.diff, args.context)

@subcommand([argument('diff')])
def patch(args):
    # Use git apply --check to test if patch can be cleanly applied.
    phabdiff = "python3 {} diff {}".format(str(spath) + "/phab.py", args.diff)
    os.system("{} | git am --keep-non-patch -3".format(phabdiff))

@subcommand()
def projects(args):
    backend.projects()

@subcommand([argument('phid')])
def project(args):
    backend.project(args.phid)

if __name__ == '__main__':
    sys.exit(main())

