from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReadingRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='阅览室名称')),
                ('open_time', models.TimeField(verbose_name='开放时间')),
                ('close_time', models.TimeField(verbose_name='关闭时间')),
                ('total_seats', models.PositiveIntegerField(default=0, verbose_name='总座位数')),
                ('rows', models.PositiveIntegerField(default=5, verbose_name='行数')),
                ('cols', models.PositiveIntegerField(default=8, verbose_name='列数')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('description', models.TextField(blank=True, verbose_name='描述')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': '阅览室',
                'verbose_name_plural': '阅览室',
            },
        ),
        migrations.CreateModel(
            name='Seat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seat_number', models.CharField(max_length=20, verbose_name='座位编号')),
                ('row', models.PositiveIntegerField(verbose_name='行号')),
                ('col', models.PositiveIntegerField(verbose_name='列号')),
                ('is_available', models.BooleanField(default=True, verbose_name='是否可用')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reading_room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='seats.readingroom', verbose_name='所属阅览室')),
            ],
            options={
                'verbose_name': '座位',
                'verbose_name_plural': '座位',
                'unique_together': {('reading_room', 'row', 'col')},
            },
        ),
        migrations.CreateModel(
            name='SeatReservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reservation_date', models.DateField(verbose_name='预约日期')),
                ('time_slot', models.CharField(choices=[('morning', '上午 (8:00-12:00)'), ('afternoon', '下午 (12:00-18:00)'), ('evening', '晚上 (18:00-22:00)')], max_length=20, verbose_name='时间段')),
                ('status', models.CharField(choices=[('pending', '待使用'), ('checked_in', '已签到'), ('completed', '已完成'), ('cancelled', '已取消'), ('no_show', '未到')], default='pending', max_length=20, verbose_name='状态')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('seat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='seats.seat', verbose_name='座位')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user', verbose_name='预约用户')),
            ],
            options={
                'verbose_name': '座位预约',
                'verbose_name_plural': '座位预约',
                'ordering': ['-reservation_date', '-created_at'],
                'unique_together': {('user', 'reservation_date', 'time_slot')},
            },
        ),
    ]
