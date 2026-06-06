from django.db import models
from apps.books.models import Book


class StockAlert(models.Model):
    ALERT_TYPE_CHOICES = (
        ('low_stock', '库存不足'),
        ('slow_moving', '长期滞销'),
        ('high_demand', '高频借阅'),
    )

    STATUS_CHOICES = (
        ('pending', '未处理'),
        ('resolved', '已处理'),
        ('ignored', '已忽略'),
    )

    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="图书")
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES, verbose_name="预警类型")
    description = models.TextField(verbose_name="预警描述")
    suggested_action = models.TextField(blank=True, verbose_name="建议操作")
    suggested_purchase_qty = models.PositiveIntegerField(default=0, verbose_name="建议采购数量")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="状态")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="生成时间")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "库存预警"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.book.title}"
