from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Notification

@login_required
def notification_list(request):
    """List user notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })

@login_required
def notification_mark_read(request, pk):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()

    # Redirect back to the link if provided, otherwise to notification list
    if notification.link:
        return redirect(notification.link)
    return redirect('notifications:notification_list')

@login_required
def notifications_mark_all_read(request):
    """Mark all user notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, _('Todas las notificaciones han sido marcadas como leídas'))
    return redirect('notifications:notification_list')
