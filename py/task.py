import re
import sys

from phabricator import Phabricator

cmd = sys.argv[1]
task = sys.argv[2]
arg = sys.argv[3]

if not task.startswith('T'):
    print("Error invalid task number -> begin with Txxxxx")
    exit(1)

transactions = []

if cmd == "description":
    description=""

    with open(arg, 'r') as fp:
        for cnt, line in enumerate(fp):
            matches = re.findall('(\[\[T\d+\]\])', line)
            if matches:
                for t in matches:
                    line = line.replace(t, t.replace('[','').replace(']', ''))
            description = description + line

    transactions.append({'type':'description',  'value':description})

if cmd == "points":
    transactions.append({'type':'points',  'value':arg})

phab = Phabricator();

task = phab.maniphest.edit(objectIdentifier=task, transactions=transactions)

