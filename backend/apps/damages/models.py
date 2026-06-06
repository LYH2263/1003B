from django.db import models
from django.core.exceptions import ValidationError
from apps.books.models import LoanRecord, Book
from apps.users.models import User


def validate_image_file(value):
    if not value.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
        raise ValidationError('只允许上传图片文件 (JPG, PNG, GIF, WEBP)。')
    if value.size > 10 * 1024 * 1024:
        raise ValidationError('图片大小不能超过 10MB。')


class DamageReport(models.Model):
    DAMAGE_LEVEL_CHOICES = (
        ('minor', '轻微'),
        ('moderate', '中度'),
        ('severe', '严重'),
        ('lost', '遗失'),
    )

    STATUS_CHOICES = (
        ('pending_assessment', '待评估'),
        ('pending_compensation', '待赔偿'),
        ('compensated', '已赔偿'),
        ('waived', '已免除'),
    )

    loan = models.OneToOneField(
        LoanRecord,
        on_delete=models.CASCADE,
        related_name='damage_report',
        verbose_name='借阅记录'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='damage_reports',
        verbose_name='图书'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='damage_reports',
        verbose_name='借阅人'
    )
    damage_level = models.CharField(
        max_length=20,
        choices=DAMAGE_LEVEL_CHOICES,
        verbose_name='损坏等级'
    )
    description = models.TextField(
        blank=True,
        verbose_name='损坏描述'
    )
    compensation_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='评估赔偿金额'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending_assessment',
        verbose_name='处理状态'
    )
    assessed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assessed_damages',
        verbose_name='评估人'
    )
    assessed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='评估时间'
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='处理完成时间'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = '损坏报告'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'损坏报告 #{self.id} - {self.book.title}'


class DamageImage(models.Model):
    damage_report = models.ForeignKey(
        DamageReport,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='损坏报告'
    )
    image = models.ImageField(
        upload_to='damage_images/',
        validators=[validate_image_file],
        verbose_name='证据照片'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='上传时间'
    )

    class Meta:
        ordering = ['uploaded_at']
        verbose_name = '损坏证据照片'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'照片 #{self.id} - 报告 #{self.damage_report_id}'
