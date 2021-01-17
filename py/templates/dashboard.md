Dashboard
=========

## Assigned Tasks

{% for t in assigned -%}
[[T{{t.id}}]] - {{t.title}}
{% endfor %}

## Responsible Diffs

{% for r in responsible['needs-review'] -%}
{% include 'item-revision.md' -%}
{% endfor %}

## Ready To Land

{% for r in responsible['accepted'] -%}
{% include 'item-revision.md' -%}
{% endfor %}

## Ready to Update

{% for r in responsible['changes-planned'] -%}
{% include 'item-revision.md' -%}
{% endfor %}


## Changes Planned
{% for r in responsible['needs-revision'] -%}
{% include 'item-revision.md' -%}
{% endfor %}

