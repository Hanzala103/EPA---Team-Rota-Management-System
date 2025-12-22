from django import template

register = template.Library()


@register.filter
def has_role(user, roles: str) -> bool:
    """
    Template filter to check if a user has any of the given role codes.
    Usage: {% if user|has_role:"rota_manager,system_admin" %} ... {% endif %}
    """
    if not user or not hasattr(user, "has_role"):
        return False

    codes = [code.strip() for code in roles.split(",") if code.strip()]
    return user.has_role(*codes)
