from django import template

from claims.models import Claim

register = template.Library()


@register.simple_tag
def asset_related_claims(asset_pk):
    """Return claims related to a specific asset"""
    return Claim.objects.filter(asset_code__iexact=f"ACT-{asset_pk:04d}").order_by(
        "-incident_date"
    )[:10]
