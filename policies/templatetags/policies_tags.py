from django import template
from ..models import Policy

register = template.Library()

@register.simple_tag
def active_policies_count():
    """Return the count of active policies"""
    return Policy.objects.filter(status='active').count()
