from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Get an item from a dictionary."""
    return dictionary.get(key, '')

@register.filter  
def replace(value, arg):
    """Replace characters in a string."""
    old, new = arg.split(',')
    return value.replace(old, new)
