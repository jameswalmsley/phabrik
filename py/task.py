import re
import sys

from phabricator import Phabricator

task = sys.argv[1]
file = sys.argv[2]

if not task.startswith('T'):
    print("Error invalid task number -> begin with Txxxxx")
    exit(1)

num = int(task[1:])


description=""

with open(file, 'r') as fp:
    for cnt, line in enumerate(fp):
        matches = re.findall('(\[\[T\d+\]\])', line)
        if matches:
            for t in matches:
                line = line.replace(t, t.replace('[','').replace(']', ''))
        description = description + line

phab = Phabricator();
task = phab.maniphest.update(id=num, description=description)

