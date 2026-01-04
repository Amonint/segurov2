from .models import UserProfile


def user_permissions(request):
    """
    Context processor to add user permissions to template context
    """
    if request.user.is_authenticated and isinstance(request.user, UserProfile):
        # Get unread notifications count and recent notifications
        unread_notifications_count = request.user.notifications.filter(is_read=False).count()
        recent_notifications = request.user.notifications.filter(is_read=False)[:5]

        return {
            'user_permissions': request.user.get_role_permissions(),
            'user_role': request.user.role,
            'user_full_name': request.user.get_full_name(),
            'unread_notifications_count': unread_notifications_count,
            'recent_notifications': recent_notifications,
        }
    return {
        'user_permissions': [],
        'user_role': None,
        'user_full_name': None,
        'unread_notifications_count': 0,
    }
