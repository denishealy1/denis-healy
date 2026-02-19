from django import template

register = template.Library()


@register.filter
def has_role(user, role):
    return getattr(user, 'role', None) == role
