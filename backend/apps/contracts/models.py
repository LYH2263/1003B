from django.db import models
from apps.books.models import LoanRecord
from django.conf import settings


class Contract(models.Model):
    STATUS_CHOICES = (
        ('pending', '待签署'),
        ('signed', '已签署'),
    )

    loan = models.OneToOneField(
        LoanRecord,
        on_delete=models.CASCADE,
        related_name='contract',
        verbose_name='借阅记录'
    )
    contract_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='合同编号'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='状态'
    )
    unsigned_pdf = models.FileField(
        upload_to='contracts/unsigned/',
        verbose_name='待签署PDF'
    )
    signed_pdf = models.FileField(
        upload_to='contracts/signed/',
        blank=True,
        null=True,
        verbose_name='已签署PDF'
    )
    signature_image = models.ImageField(
        upload_to='signatures/',
        blank=True,
        null=True,
        verbose_name='签名图片'
    )
    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='签署时间'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = '借阅合同'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'合同-{self.contract_number}'
