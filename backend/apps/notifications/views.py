from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Notification


@login_required
def get_notifications(request):
    notification_type = request.GET.get('type', '')
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    
    notifications = Notification.objects.filter(recipient=request.user)
    
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    start = (page - 1) * page_size
    end = start + page_size
    notifications_page = notifications[start:end]
    
    data = {
        'notifications': [{
            'id': n.id,
            'type': n.notification_type,
            'type_display': n.get_notification_type_display(),
            'title': n.title,
            'content': n.content,
            'related_object_id': n.related_object_id,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for n in notifications_page],
        'total': notifications.count(),
        'page': page,
        'page_size': page_size,
        'unread_count': Notification.get_unread_count(request.user)
    }
    
    return JsonResponse(data)


@login_required
@require_http_methods(['POST'])
def mark_as_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    return JsonResponse({
        'success': True,
        'unread_count': Notification.get_unread_count(request.user)
    })


@login_required
@require_http_methods(['POST'])
def mark_all_as_read(request):
    Notification.mark_all_as_read(request.user)
    
    return JsonResponse({
        'success': True,
        'unread_count': 0
    })


@login_required
def get_unread_count(request):
    return JsonResponse({
        'count': Notification.get_unread_count(request.user)
    })
