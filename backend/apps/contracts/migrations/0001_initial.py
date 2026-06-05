from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('books', '0004_book_preview_file'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contract_number', models.CharField(max_length=50, unique=True, verbose_name='合同编号')),
                ('status', models.CharField(choices=[('pending', '待签署'), ('signed', '已签署')], default='pending', max_length=20, verbose_name='状态')),
                ('unsigned_pdf', models.FileField(upload_to='contracts/unsigned/', verbose_name='待签署PDF')),
                ('signed_pdf', models.FileField(blank=True, null=True, upload_to='contracts/signed/', verbose_name='已签署PDF')),
                ('signature_image', models.ImageField(blank=True, null=True, upload_to='signatures/', verbose_name='签名图片')),
                ('signed_at', models.DateTimeField(blank=True, null=True, verbose_name='签署时间')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('loan', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='contract', to='books.loanrecord', verbose_name='借阅记录')),
            ],
            options={
                'verbose_name': '借阅合同',
                'verbose_name_plural': '借阅合同',
                'ordering': ['-created_at'],
            },
        ),
    ]
