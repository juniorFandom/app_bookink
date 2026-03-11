from django import template

register = template.Library()

@register.filter
def field_label(form, field_name):
    try:
        return form.fields[field_name].label or field_name.replace('_', ' ').capitalize()
    except Exception:
        return field_name.replace('_', ' ').capitalize() 