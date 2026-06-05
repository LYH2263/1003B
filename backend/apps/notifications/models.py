from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = (
        ('borrow_audit', '借阅审核'),
        ('due_reminder', '到期提醒'),
        ('system_announcement', '系统公告'),
        ('transfer_notice', '转借通知'),
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='接收人'
    )
    notification_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        verbose_name='类型'
    )
    title = models.CharField(max_length=100, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    related_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='关联对象ID'
    )
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        ordering = ['-created_at']
        verbose_name = '通知'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.get_notification_type_display()} - {self.title}'

    @classmethod
    def get_unread_count(cls, user):
        return cls.objects.filter(recipient=user, is_read=False).count()

    @classmethod
    def mark_all_as_read(cls, user):
        cls.objects.filter(recipient=user, is_read=False).update(is_read=True)
