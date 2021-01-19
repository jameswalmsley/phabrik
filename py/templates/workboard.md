# {{project.name}} {{project.id}}

{% for col in project.columns %}
{{col.name}}
{{ "-"*col.name|length }}

{% for t in col.tasks -%}
T{{t.id}} - {{ utils.get_priority_symbol(t.priority['name']) }} - {{t.name}}
{% endfor %}
{% endfor %}
