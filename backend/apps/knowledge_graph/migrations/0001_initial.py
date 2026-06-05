from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('books', '0004_book_preview_file'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookRelation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relation_type', models.CharField(choices=[('same_author', '同作者'), ('same_category', '同分类'), ('series', '系列作品'), ('also_read', '读者也在读'), ('topic_related', '主题相关')], max_length=20, verbose_name='关系类型')),
                ('weight', models.PositiveIntegerField(default=5, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)], verbose_name='权重')),
                ('is_manual', models.BooleanField(default=False, verbose_name='是否手动添加')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('source_book', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='outgoing_relations', to='books.book', verbose_name='源图书')),
                ('target_book', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='incoming_relations', to='books.book', verbose_name='目标图书')),
            ],
            options={
                'verbose_name': '图书关联关系',
                'verbose_name_plural': '图书关联关系',
                'ordering': ['-weight', '-created_at'],
                'unique_together': {('source_book', 'target_book', 'relation_type')},
            },
        ),
    ]
