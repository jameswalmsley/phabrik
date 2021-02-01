---
{{frontmatter}}
---

{{description}}

+++

Revisions:
================================================================================

Key: 🟣 - published        🟢 - accepted         🟠 - needs-review     🔵 - draft
     🔴 - changes-planned  🔨 - needs-revision   🛫 - abandoned


--------------------------------------------------------------------------------

{% for rev in task.revisions -%}
{{rev.name}} - {{utils.get_diff_status_symbol(rev.status)}} - {{rev.title}}
{% endfor %}
--------------------------------------------------------------------------------

Comments:
================================================================================

{% for c in task.comments|reverse -%}
{% if not c.removed -%}
{{utils.justify_strings(c.author.name + " ({})".format(c.author.username), "`{}`".format(c.created), 81)}}
--------------------------------------------------------------------------------

{{c.text}}
{% endif -%}
{% endfor %}

::: Add Comment
--------------------------------------------------------------------------------


+++
