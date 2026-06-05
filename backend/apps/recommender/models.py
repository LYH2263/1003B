from django.db import models
from apps.users.models import User
from django.utils import timezone
import json

class RecommendationCache(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='用户', related_name='recommendation_cache')
    recommendations = models.JSONField(verbose_name='推荐图书列表')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='生成时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        ordering = ['-updated_at']
        verbose_name = '推荐缓存'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.user.username} 的推荐'

    def get_recommendations(self):
        return self.recommendations if isinstance(self.recommendations, list) else json.loads(self.recommendations)
