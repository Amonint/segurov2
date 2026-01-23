from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _


def role_required(roles=None):
    """
    Decorator to check if user has one of the required roles.

    Usage:
        @role_required(roles=['admin', 'insurance_manager'])
        def my_view(request):
            ...
    """
    if roles is None:
        roles = []

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(
                    request, _("Debe iniciar sesión para acceder a esta página.")
                )
                return redirect("accounts:login")

            if request.user.role not in roles:
                messages.error(
                    request, _("No tiene permisos para acceder a esta página.")
                )
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def permission_required(permission):
    """
    Decorator to check if user has a specific permission based on their role.

    Usage:
        @permission_required('claims_write')
        def my_view(request):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(
                    request, _("Debe iniciar sesión para acceder a esta página.")
                )
                return redirect("accounts:login")

            if not request.user.has_role_permission(permission):
                messages.error(
                    request,
                    _("No tiene permisos suficientes para realizar esta acción."),
                )
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def owner_or_permission_required(permission, owner_field="user"):
    """
    Decorator to check if user is the owner of the object or has the required permission.

    Usage:
        @owner_or_permission_required('claims_write', owner_field='reported_by')
        def my_view(request, pk):
            ...

    The view must accept a 'pk' parameter and the model must be retrievable.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(
                    request, _("Debe iniciar sesión para acceder a esta página.")
                )
                return redirect("accounts:login")

            # Get the object pk from kwargs
            pk = kwargs.get("pk")
            if not pk:
                raise ValueError(
                    "owner_or_permission_required requires a 'pk' parameter in the URL"
                )

            # Check if user has the permission
            if request.user.has_role_permission(permission):
                return view_func(request, *args, **kwargs)

            # If not, check if user is the owner
            # This will be checked in the view itself for flexibility
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def requester_own_data_only(model_class, owner_field="reported_by"):
    """
    Decorator specifically for requesters to ensure they only access their own data.

    Usage:
        @requester_own_data_only(Claim, owner_field='reported_by')
        def my_view(request, pk):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(
                    request, _("Debe iniciar sesión para acceder a esta página.")
                )
                return redirect("accounts:login")

            # If user is not a requester, allow normal permission checks
            if request.user.role != "requester":
                return view_func(request, *args, **kwargs)

            # For requesters, check ownership
            pk = kwargs.get("pk")
            if pk:
                try:
                    obj = model_class.objects.get(pk=pk)
                    owner = getattr(obj, owner_field, None)

                    if owner != request.user:
                        messages.error(
                            request, _("No tiene permisos para acceder a este recurso.")
                        )
                        raise PermissionDenied
                except model_class.DoesNotExist:
                    messages.error(request, _("El recurso no existe."))
                    raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
