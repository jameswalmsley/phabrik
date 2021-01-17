# Phabrik

Phabrik is a toolkit for developers to interact with Phabricator. Its main focus is to
allow developers to create and edit tasks without having to use the web-interface.

It further allows a streamlined workflow, and supports simple interactions with repositories
and revisions.

## Plugins

Currently phabrik support NeoVim, but we are moving to full ViM compatibility.
The main tooling is written in python, and can be used to create a plugin for any
text editor.


## Current Features

Allows users to sync their phabricator tasks with vimwiki, and modify and update them conveniently.

  * Task titles, points, and assigned user can be updated using frontmatter.
  * Task discussion threads.
  * Comments can be added to a task discussion.
  * Differentials are listed in the "backmatter" and can be previewed.
  * DIFF status is displayed.
  * DIFFs can be accepted.

## Install

```
Plug 'jameswalmsley/phabrik', {'do': ':lua phab.install()'}
```

## Features

  * Tasks
    * View Task
    * Read Task Comments
    * Add new comments
    * Read Task revisions.
    * Change points
    * View / Change assignee
    * View Tags
    * View Projects

  * Revisions
    * View Diffs
    * Patch Diffs
    * Accept Diffs

