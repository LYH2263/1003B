from django.core.management.base import BaseCommand
from apps.users.models import User
from apps.recommender.services import cache_recommendations
from django.utils import timezone

class Command(BaseCommand):
    help = '为所有用户批量重新计算推荐结果'

    def handle(self, *args, **options):
        start_time = timezone.now()
        self.stdout.write(self.style.NOTICE(f'开始计算推荐结果: {start_time}'))
        
        readers = User.objects.filter(role='reader')
        total = readers.count()
        success = 0
        
        for i, user in enumerate(readers, 1):
            try:
                cache_recommendations(user)
                success += 1
                if i % 10 == 0 or i == total:
                    self.stdout.write(f'  进度: {i}/{total} ({i/total*100:.1f}%)')
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'  用户 {user.username} 计算失败: {e}'))
        
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        
        self.stdout.write(self.style.SUCCESS(f'\n计算完成!'))
        self.stdout.write(f'  总用户数: {total}')
        self.stdout.write(f'  成功: {success}')
        self.stdout.write(f'  失败: {total - success}')
        self.stdout.write(f'  耗时: {duration:.2f} 秒')
