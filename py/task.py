import sys

from phabricator import Phabricator

task = sys.argv[1]
file = sys.argv[2]

if not task.startswith('T'):
    print("Error invalid task number -> begin with Txxxxx")
    exit(1)

num = int(task[1:])

s = open(file, 'r').read()

phab = Phabricator();
task = phab.maniphest.update(id=num, description=s)

