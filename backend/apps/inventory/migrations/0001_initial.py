from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('books', '0005_alter_book_isbn'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alert_type', models.CharField(choices=[('low_stock', '库存不足'), ('slow_moving', '长期滞销'), ('high_demand', '高频借阅')], max_length=20, verbose_name='预警类型')),
                ('description', models.TextField(verbose_name='预警描述')),
                ('suggested_action', models.TextField(blank=True, verbose_name='建议操作')),
                ('suggested_purchase_qty', models.PositiveIntegerField(default=0, verbose_name='建议采购数量')),
                ('status', models.CharField(choices=[('pending', '未处理'), ('resolved', '已处理'), ('ignored', '已忽略')], default='pending', max_length=20, verbose_name='状态')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='生成时间')),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='books.book', verbose_name='图书')),
            ],
            options={
                'verbose_name': '库存预警',
                'verbose_name_plural': '库存预警',
                'ordering': ['-created_at'],
            },
        ),
    ]
