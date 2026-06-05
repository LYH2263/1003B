from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Recommendation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='书名')),
                ('author', models.CharField(max_length=50, verbose_name='作者')),
                ('publisher', models.CharField(blank=True, max_length=100, verbose_name='出版社')),
                ('reason', models.TextField(verbose_name='推荐理由')),
                ('urgency', models.CharField(choices=[('normal', '普通'), ('urgent', '较急'), ('very_urgent', '非常期待')], default='normal', max_length=20, verbose_name='紧急程度')),
                ('status', models.CharField(choices=[('pending', '待审核'), ('approved', '已采纳'), ('rejected', '已拒绝')], default='pending', max_length=20, verbose_name='状态')),
                ('admin_reply', models.TextField(blank=True, verbose_name='管理员回复')),
                ('reviewed_at', models.DateTimeField(blank=True, null=True, verbose_name='审核时间')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='提交时间')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user', verbose_name='推荐人')),
            ],
            options={
                'verbose_name': '荐书推荐',
                'verbose_name_plural': '荐书推荐',
                'ordering': ['-created_at'],
            },
        ),
    ]
