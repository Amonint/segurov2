from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import AuditLog
import json


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log user actions
    """

    def process_request(self, request):
        """
        Store request information for later use in logging
        """
        # This middleware mainly ensures audit logging is active
        # The actual logging happens through signals
        pass


# Signal handlers for automatic audit logging

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Log user login events
    """
    # Get IP address and user agent from request
    ip_address = get_client_ip_from_request(request)
    user_agent = request.META.get('HTTP_USER_AGENT')

    AuditLog.log_action(
        user=user,
        action_type='login',
        entity_type='user',
        entity_id=str(user.id),
        description=f'Inicio de sesión del usuario {user.get_full_name()}',
        ip_address=ip_address,
        user_agent=user_agent
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Log user logout events
    """
    # Get IP address and user agent from request
    ip_address = get_client_ip_from_request(request)
    user_agent = request.META.get('HTTP_USER_AGENT')

    AuditLog.log_action(
        user=user,
        action_type='logout',
        entity_type='user',
        entity_id=str(user.id),
        description=f'Cierre de sesión del usuario {user.get_full_name()}',
        ip_address=ip_address,
        user_agent=user_agent
    )


def get_client_ip_from_request(request):
    """
    Get client IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_model_entity_type(model):
    """
    Map Django model to entity type
    """
    model_mapping = {
        'UserProfile': 'user',
        'Policy': 'policy',
        'Claim': 'claim',
        'Invoice': 'invoice',
        'Asset': 'asset',
        'InsuranceCompany': 'insurance_company',
        'Broker': 'broker',
        'Notification': 'notification',
    }
    return model_mapping.get(model.__name__, 'unknown')


# Temporarily disable automatic model auditing to avoid issues during development
# These can be re-enabled once the system is stable

# @receiver(post_save)
# def log_model_save(sender, instance, created, **kwargs):
#     """
#     Log model save events (create/update)
#     """
#     # Skip audit logs themselves to avoid recursion
#     if sender.__name__ == 'AuditLog':
#         return
#
#     # For now, only log if we have a user associated with the instance
#     user = None
#     if hasattr(instance, 'created_by') and instance.created_by:
#         user = instance.created_by
#     elif hasattr(instance, 'uploaded_by') and instance.uploaded_by:
#         user = instance.uploaded_by
#     elif hasattr(instance, 'user') and instance.user:
#         user = instance.user
#
#     if not user:
#         return  # Don't log if no user available
#
#     action_type = 'create' if created else 'update'
#     entity_type = get_model_entity_type(sender)
#
#     # Convert instance to dict for logging
#     try:
#         new_values = {
#             field.name: str(getattr(instance, field.name))
#             for field in instance._meta.fields
#             if field.name not in ['password', 'created_at', 'updated_at']
#         }
#     except:
#         new_values = {'id': instance.id}
#
#     description = f'{"Creación" if created else "Actualización"} de {sender._meta.verbose_name}'
#
#     AuditLog.log_action(
#         user=user,
#         action_type=action_type,
#         entity_type=entity_type,
#         entity_id=str(instance.id),
#         description=description,
#         new_values=new_values
#     )


# @receiver(post_delete)
# def log_model_delete(sender, instance, **kwargs):
#     """
#     Log model delete events
#     """
#     # Skip audit logs themselves
#     if sender.__name__ == 'AuditLog':
#         return
#
#     # Similar user detection logic as above
#     user = None
#     if hasattr(instance, 'created_by') and instance.created_by:
#         user = instance.created_by
#     elif hasattr(instance, 'uploaded_by') and instance.uploaded_by:
#         user = instance.uploaded_by
#
#     if not user:
#         return
#
#     entity_type = get_model_entity_type(sender)
#
#     # Convert instance to dict for logging
#     try:
#         old_values = {
#             field.name: str(getattr(instance, field.name))
#             for field in instance._meta.fields
#             if field.name not in ['password', 'created_at', 'updated_at']
#         }
#     except:
#         old_values = {'id': instance.id}
#
#     description = f'Eliminación de {sender._meta.verbose_name}'
#
#     AuditLog.log_action(
#         user=user,
#         action_type='delete',
#         entity_type=entity_type,
#         entity_id=str(instance.id),
#         description=description,
#         old_values=old_values
#     )
