from django import template

register = template.Library()


@register.filter
def split(value, arg):
    """Split a string by a separator and return a list"""
    if not value:
        return []
    return [item.strip() for item in value.split(arg)]


@register.filter
def divide(value, arg):
    """Divide two numbers"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0


@register.filter
def strip(value):
    """Strip whitespace from string"""
    return str(value).strip()


@register.filter
def mul(value, arg):
    """Multiply two numbers"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
