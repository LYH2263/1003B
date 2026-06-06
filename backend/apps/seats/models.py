from django.db import models
from apps.users.models import User
from django.core.exceptions import ValidationError
from datetime import date


class ReadingRoom(models.Model):
    name = models.CharField(max_length=100, verbose_name="阅览室名称")
    open_time = models.TimeField(verbose_name="开放时间")
    close_time = models.TimeField(verbose_name="关闭时间")
    total_seats = models.PositiveIntegerField(verbose_name="总座位数", default=0)
    rows = models.PositiveIntegerField(verbose_name="行数", default=5)
    cols = models.PositiveIntegerField(verbose_name="列数", default=8)
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    description = models.TextField(blank=True, verbose_name="描述")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "阅览室"
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        self.total_seats = self.rows * self.cols
        super().save(*args, **kwargs)


class Seat(models.Model):
    reading_room = models.ForeignKey(ReadingRoom, on_delete=models.CASCADE, verbose_name="所属阅览室")
    seat_number = models.CharField(max_length=20, verbose_name="座位编号")
    row = models.PositiveIntegerField(verbose_name="行号")
    col = models.PositiveIntegerField(verbose_name="列号")
    is_available = models.BooleanField(default=True, verbose_name="是否可用")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reading_room.name} - {self.seat_number}"

    class Meta:
        verbose_name = "座位"
        verbose_name_plural = verbose_name
        unique_together = ['reading_room', 'row', 'col']


class SeatReservation(models.Model):
    TIME_SLOT_CHOICES = (
        ('morning', '上午 (8:00-12:00)'),
        ('afternoon', '下午 (12:00-18:00)'),
        ('evening', '晚上 (18:00-22:00)'),
    )

    STATUS_CHOICES = (
        ('pending', '待使用'),
        ('checked_in', '已签到'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
        ('no_show', '未到'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="预约用户")
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, verbose_name="座位")
    reservation_date = models.DateField(verbose_name="预约日期")
    time_slot = models.CharField(max_length=20, choices=TIME_SLOT_CHOICES, verbose_name="时间段")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="状态")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.seat.seat_number} - {self.reservation_date}"

    class Meta:
        verbose_name = "座位预约"
        verbose_name_plural = verbose_name
        ordering = ['-reservation_date', '-created_at']

    def clean(self):
        if SeatReservation.objects.filter(
            user=self.user,
            reservation_date=self.reservation_date,
            time_slot=self.time_slot,
            status__in=['pending', 'checked_in']
        ).exclude(pk=self.pk).exists():
            raise ValidationError("同一用户同一天同一时间段只能预约一个座位")

        if SeatReservation.objects.filter(
            seat=self.seat,
            reservation_date=self.reservation_date,
            time_slot=self.time_slot,
            status__in=['pending', 'checked_in']
        ).exclude(pk=self.pk).exists():
            raise ValidationError("该座位在此时间段已被预约")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
