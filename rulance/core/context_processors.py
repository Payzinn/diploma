from .models import Notification

def unread_notifications(request):
    if request.user.is_authenticated:
        return {
            'unread_count': Notification.objects.filter(user=request.user, is_read=False).count()
        }
    return {}
