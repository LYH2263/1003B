from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecommendationCache',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recommendations', models.JSONField(verbose_name='推荐图书列表')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='生成时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='recommendation_cache', to='users.user', verbose_name='用户')),
            ],
            options={
                'verbose_name': '推荐缓存',
                'verbose_name_plural': '推荐缓存',
                'ordering': ['-updated_at'],
            },
        ),
    ]
