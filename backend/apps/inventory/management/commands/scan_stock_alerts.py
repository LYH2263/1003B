from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.inventory.services import scan_and_generate_alerts


class Command(BaseCommand):
    help = '扫描图书库存，生成智能预警'

    def handle(self, *args, **options):
        start_time = timezone.now()
        self.stdout.write(self.style.NOTICE(f'开始库存预警扫描: {start_time}'))

        result = scan_and_generate_alerts()

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        self.stdout.write(self.style.SUCCESS('\n扫描完成!'))
        self.stdout.write(f'  扫描图书总数: {result["total_books"]}')
        self.stdout.write(f'  新增预警: {result["new_alerts"]}')
        self.stdout.write(f'  跳过已有预警: {result["skipped"]}')
        self.stdout.write(f'  耗时: {duration:.2f} 秒')
