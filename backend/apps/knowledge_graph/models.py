from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.books.models import Book


class BookRelation(models.Model):
    RELATION_TYPE_CHOICES = (
        ('same_author', '同作者'),
        ('same_category', '同分类'),
        ('series', '系列作品'),
        ('also_read', '读者也在读'),
        ('topic_related', '主题相关'),
    )

    RELATION_COLORS = {
        'same_author': '#3B82F6',
        'same_category': '#10B981',
        'series': '#8B5CF6',
        'also_read': '#F59E0B',
        'topic_related': '#EF4444',
    }

    source_book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='outgoing_relations',
        verbose_name='源图书'
    )
    target_book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='incoming_relations',
        verbose_name='目标图书'
    )
    relation_type = models.CharField(
        max_length=20,
        choices=RELATION_TYPE_CHOICES,
        verbose_name='关系类型'
    )
    weight = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='权重'
    )
    is_manual = models.BooleanField(
        default=False,
        verbose_name='是否手动添加'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )

    class Meta:
        verbose_name = '图书关联关系'
        verbose_name_plural = verbose_name
        unique_together = ['source_book', 'target_book', 'relation_type']
        ordering = ['-weight', '-created_at']

    def __str__(self):
        return f'{self.source_book.title} → {self.target_book.title} ({self.get_relation_type_display()})'

    def get_color(self):
        return self.RELATION_COLORS.get(self.relation_type, '#6B7280')

    @classmethod
    def get_all_relations_for_book(cls, book, depth=1):
        visited = set()
        relations = []
        books = {book}

        def dfs(current_book, current_depth):
            if current_depth > depth or current_book.id in visited:
                return
            visited.add(current_book.id)

            outgoing = cls.objects.filter(source_book=current_book).select_related('source_book', 'target_book')
            for rel in outgoing:
                relations.append(rel)
                books.add(rel.target_book)
                dfs(rel.target_book, current_depth + 1)

            incoming = cls.objects.filter(target_book=current_book).select_related('source_book', 'target_book')
            for rel in incoming:
                relations.append(rel)
                books.add(rel.source_book)
                dfs(rel.source_book, current_depth + 1)

        dfs(book, 0)
        return books, relations
