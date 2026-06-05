import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification


def send_notification(recipient, notification_type, title, content, related_object_id=None):
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        content=content,
        related_object_id=related_object_id
    )
    
    channel_layer = get_channel_layer()
    user_group_name = f'user_{recipient.id}'
    
    notification_data = {
        'id': notification.id,
        'type': notification.notification_type,
        'type_display': notification.get_notification_type_display(),
        'title': notification.title,
        'content': notification.content,
        'related_object_id': notification.related_object_id,
        'is_read': notification.is_read,
        'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    async_to_sync(channel_layer.group_send)(
        user_group_name,
        {
            'type': 'send_notification',
            'notification': notification_data
        }
    )
    
    unread_count = Notification.get_unread_count(recipient)
    async_to_sync(channel_layer.group_send)(
        user_group_name,
        {
            'type': 'update_unread_count',
            'count': unread_count
        }
    )
    
    return notification
