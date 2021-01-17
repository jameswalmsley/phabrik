```
      ___      ___         ___                     ___                   ___
     /  /\    /__/\       /  /\       _____       /  /\      ___        /__/|
    /  /::\   \  \:\     /  /::\     /  /::\     /  /::\    /  /\      |  |:|
   /  /:/\:\   \__\:\   /  /:/\:\   /  /:/\:\   /  /:/\:\  /  /:/      |  |:|
  /  /:/~/:___ /  /::\ /  /:/~/::\ /  /:/~/::\ /  /:/~/:/ /__/::\    __|  |:|
 /__/:/ /:/__/\  /:/\:/__/:/ /:/\:/__/:/ /:/\:/__/:/ /:/__\__\/\:\__/__/\_|:|____
 \  \:\/:/\  \:\/:/__\\  \:\/:/__\\  \:\/:/~/:\  \:\/:::::/  \  \:\/\  \:\/:::::/
  \  \::/  \  \::/     \  \::/     \  \::/ /:/ \  \::/~~~~    \__\::/\  \::/~~~~
   \  \:\   \  \:\      \  \:\      \  \:\/:/   \  \:\        /__/:/  \  \:\
    \  \:\   \  \:\      \  \:\      \  \::/     \  \:\       \__\/    \  \:\
     \__\/    \__\/       \__\/       \__\/       \__\/                 \__\/

```
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


```
Copyright (C) 2021 James Walmsley <james@fullfat-fs.co.uk>
Copyright (C) 2021 Vital Element Solutions Ltd <james@vitalelement.co.uk>

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

```
