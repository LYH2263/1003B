from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.books.models import Book, LoanRecord
from apps.knowledge_graph.models import BookRelation
from collections import defaultdict


class Command(BaseCommand):
    help = '批量扫描并自动生成图书关联关系'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='清除所有自动生成的关系后重新生成',
        )
        parser.add_argument(
            '--types',
            type=str,
            default='all',
            help='指定生成的关系类型，多个用逗号分隔: same_author,also_read,all',
        )

    def handle(self, *args, **options):
        start_time = timezone.now()
        self.stdout.write(self.style.NOTICE(f'开始生成图书关联关系: {start_time}'))

        clear_existing = options['clear']
        types = options['types'].split(',') if options['types'] != 'all' else ['same_author', 'also_read']

        if clear_existing:
            deleted, _ = BookRelation.objects.filter(is_manual=False).delete()
            self.stdout.write(self.style.WARNING(f'已清除 {deleted} 条自动生成的关系'))

        total_created = 0

        if 'same_author' in types:
            count = self.generate_same_author_relations()
            total_created += count
            self.stdout.write(self.style.SUCCESS(f'同作者关系: 生成 {count} 条'))

        if 'also_read' in types:
            count = self.generate_also_read_relations()
            total_created += count
            self.stdout.write(self.style.SUCCESS(f'读者也在读关系: 生成 {count} 条'))

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        self.stdout.write(self.style.SUCCESS(f'\n生成完成!'))
        self.stdout.write(f'  总关系数: {total_created}')
        self.stdout.write(f'  耗时: {duration:.2f} 秒')

    def generate_same_author_relations(self):
        created_count = 0
        books = Book.objects.select_related('category').order_by('author')
        author_books = defaultdict(list)

        for book in books:
            if book.author:
                author_books[book.author].append(book)

        for author, book_list in author_books.items():
            if len(book_list) < 2:
                continue

            for i, book1 in enumerate(book_list):
                for book2 in book_list[i + 1:min(i + 6, len(book_list))]:
                    with transaction.atomic():
                        rel1, created1 = BookRelation.objects.get_or_create(
                            source_book=book1,
                            target_book=book2,
                            relation_type='same_author',
                            defaults={'weight': 8, 'is_manual': False}
                        )
                        rel2, created2 = BookRelation.objects.get_or_create(
                            source_book=book2,
                            target_book=book1,
                            relation_type='same_author',
                            defaults={'weight': 8, 'is_manual': False}
                        )
                        if created1 or created2:
                            created_count += 1

        return created_count

    def generate_also_read_relations(self):
        created_count = 0
        user_books = defaultdict(set)

        loans = LoanRecord.objects.filter(
            status__in=['borrowed', 'returned']
        ).select_related('user', 'book', 'book__category')

        for loan in loans:
            if loan.book.category:
                user_books[loan.user_id].add(loan.book)

        for user_id, books in user_books.items():
            if len(books) < 2:
                continue

            category_groups = defaultdict(list)
            for book in books:
                if book.category:
                    category_groups[book.category.id].append(book)

            for category_id, book_list in category_groups.items():
                if len(book_list) < 2:
                    continue

                for i, book1 in enumerate(book_list):
                    for book2 in book_list[i + 1:]:
                        weight = min(6, 10)
                        with transaction.atomic():
                            rel1, created1 = BookRelation.objects.get_or_create(
                                source_book=book1,
                                target_book=book2,
                                relation_type='also_read',
                                defaults={'weight': weight, 'is_manual': False}
                            )
                            rel2, created2 = BookRelation.objects.get_or_create(
                                source_book=book2,
                                target_book=book1,
                                relation_type='also_read',
                                defaults={'weight': weight, 'is_manual': False}
                            )
                            if created1 or created2:
                                created_count += 1

        return created_count
