from django.db import models
from apps.users.models import User

class Recommendation(models.Model):
    STATUS_CHOICES = (
        ('pending', '待审核'),
        ('approved', '已采纳'),
        ('rejected', '已拒绝'),
    )
    
    URGENCY_CHOICES = (
        ('normal', '普通'),
        ('urgent', '较急'),
        ('very_urgent', '非常期待'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="推荐人")
    title = models.CharField(max_length=100, verbose_name="书名")
    author = models.CharField(max_length=50, verbose_name="作者")
    publisher = models.CharField(max_length=100, blank=True, verbose_name="出版社")
    reason = models.TextField(verbose_name="推荐理由")
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='normal', verbose_name="紧急程度")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="状态")
    admin_reply = models.TextField(blank=True, verbose_name="管理员回复")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="审核时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="提交时间")
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "荐书推荐"
        verbose_name_plural = verbose_name
