from .models import Notification

def notifications(request):
    if not request.user.is_authenticated:
        return {}
    qs = request.user.notifications.all()
    return {
        'notifications': qs,
        'unread_count': qs.filter(is_read=False).count(),
    }

