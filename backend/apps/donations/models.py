from django.db import models
from django.utils import timezone
from apps.users.models import User


class Donation(models.Model):
    STATUS_CHOICES = (
        ('pending', '待审核'),
        ('received', '已接收'),
        ('stocked', '已入库'),
        ('rejected', '已拒绝'),
    )

    CONDITION_CHOICES = (
        ('new', '全新'),
        ('like_new', '几乎全新'),
        ('good', '良好'),
        ('fair', '一般'),
        ('poor', '破旧'),
    )

    tracking_number = models.CharField(max_length=20, unique=True, verbose_name='追踪编号')
    donor_name = models.CharField(max_length=50, verbose_name='捐赠人姓名')
    donor_phone = models.CharField(max_length=20, verbose_name='联系电话')
    donor_email = models.EmailField(blank=True, null=True, verbose_name='邮箱')
    remark = models.TextField(blank=True, verbose_name='备注')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    admin_note = models.TextField(blank=True, verbose_name='管理员备注')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_donations', verbose_name='审核人')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='提交时间')

    class Meta:
        ordering = ['-created_at']
        verbose_name = '捐赠记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.tracking_number} - {self.donor_name}'

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()
        super().save(*args, **kwargs)

    @classmethod
    def generate_tracking_number(cls):
        date_str = timezone.now().strftime('%Y%m%d')
        prefix = f'DN{date_str}'
        last_donation = cls.objects.filter(tracking_number__startswith=prefix).order_by('-tracking_number').first()
        if last_donation:
            last_num = int(last_donation.tracking_number[-4:])
            new_num = str(last_num + 1).zfill(4)
        else:
            new_num = '0001'
        return f'{prefix}{new_num}'

    def get_total_books(self):
        return sum(book.quantity for book in self.books.all())

    def get_condition_display_cn(self, condition):
        condition_map = dict(self.CONDITION_CHOICES)
        return condition_map.get(condition, condition)


class DonationBook(models.Model):
    CONDITION_CHOICES = (
        ('new', '全新'),
        ('like_new', '几乎全新'),
        ('good', '良好'),
        ('fair', '一般'),
        ('poor', '破旧'),
    )

    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name='books', verbose_name='捐赠记录')
    title = models.CharField(max_length=100, verbose_name='书名')
    author = models.CharField(max_length=50, verbose_name='作者')
    isbn = models.CharField(max_length=20, blank=True, verbose_name='ISBN')
    quantity = models.PositiveIntegerField(default=1, verbose_name='数量')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good', verbose_name='新旧程度')
    added_to_library = models.BooleanField(default=False, verbose_name='已入库')

    class Meta:
        verbose_name = '捐赠图书'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.title} ({self.quantity}本)'

    def get_condition_display_cn(self):
        condition_map = dict(self.CONDITION_CHOICES)
        return condition_map.get(self.condition, self.condition)
