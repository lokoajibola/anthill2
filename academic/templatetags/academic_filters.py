from django import template

register = template.Library()

@register.filter
def groupby(value, arg):
    """Group a list of objects by an attribute"""
    from itertools import groupby
    from django.utils.html import conditional_escape
    from django.utils.safestring import mark_safe
    
    value.sort(key=lambda x: getattr(x, arg))
    groups = []
    for key, group in groupby(value, lambda x: getattr(x, arg)):
        groups.append((key, list(group)))
    return groups


@register.filter
def get_item(dictionary, key):
    """Get a value from a dictionary by key"""
    return dictionary.get(key)