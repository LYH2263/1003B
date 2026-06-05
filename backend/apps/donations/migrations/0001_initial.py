from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Donation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tracking_number', models.CharField(max_length=20, unique=True, verbose_name='追踪编号')),
                ('donor_name', models.CharField(max_length=50, verbose_name='捐赠人姓名')),
                ('donor_phone', models.CharField(max_length=20, verbose_name='联系电话')),
                ('donor_email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='邮箱')),
                ('remark', models.TextField(blank=True, verbose_name='备注')),
                ('status', models.CharField(choices=[('pending', '待审核'), ('received', '已接收'), ('stocked', '已入库'), ('rejected', '已拒绝')], default='pending', max_length=20, verbose_name='状态')),
                ('admin_note', models.TextField(blank=True, verbose_name='管理员备注')),
                ('reviewed_at', models.DateTimeField(blank=True, null=True, verbose_name='审核时间')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='提交时间')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_donations', to='users.user', verbose_name='审核人')),
            ],
            options={
                'verbose_name': '捐赠记录',
                'verbose_name_plural': '捐赠记录',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DonationBook',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='书名')),
                ('author', models.CharField(max_length=50, verbose_name='作者')),
                ('isbn', models.CharField(blank=True, max_length=20, verbose_name='ISBN')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='数量')),
                ('condition', models.CharField(choices=[('new', '全新'), ('like_new', '几乎全新'), ('good', '良好'), ('fair', '一般'), ('poor', '破旧')], default='good', max_length=20, verbose_name='新旧程度')),
                ('added_to_library', models.BooleanField(default=False, verbose_name='已入库')),
                ('donation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='books', to='donations.donation', verbose_name='捐赠记录')),
            ],
            options={
                'verbose_name': '捐赠图书',
                'verbose_name_plural': '捐赠图书',
            },
        ),
    ]
