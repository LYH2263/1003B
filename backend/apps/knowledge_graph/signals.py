from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
from apps.books.models import Book, LoanRecord
from .models import BookRelation

_previous_status = {}


@receiver(pre_save, sender=LoanRecord)
def capture_previous_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = LoanRecord.objects.get(pk=instance.pk)
            _previous_status[instance.pk] = old_instance.status
        except LoanRecord.DoesNotExist:
            _previous_status[instance.pk] = None


@receiver(post_save, sender=Book)
def create_author_relations(sender, instance, created, **kwargs):
    if not created:
        return

    if not instance.author:
        return

    same_author_books = Book.objects.filter(
        author=instance.author
    ).exclude(pk=instance.pk)

    for book in same_author_books[:5]:
        BookRelation.objects.get_or_create(
            source_book=instance,
            target_book=book,
            relation_type='same_author',
            defaults={'weight': 8, 'is_manual': False}
        )
        BookRelation.objects.get_or_create(
            source_book=book,
            target_book=instance,
            relation_type='same_author',
            defaults={'weight': 8, 'is_manual': False}
        )


@receiver(post_save, sender=LoanRecord)
def create_loan_based_relations(sender, instance, created, **kwargs):
    old_status = _previous_status.pop(instance.pk, None)

    if created:
        status_just_became_active = instance.status in ['borrowed', 'returned']
    else:
        status_just_became_active = (
            old_status not in ['borrowed', 'returned']
            and instance.status in ['borrowed', 'returned']
        )

    if not status_just_became_active:
        return

    user = instance.user
    current_book = instance.book

    user_loans = LoanRecord.objects.filter(
        user=user,
        status__in=['borrowed', 'returned']
    ).exclude(book=current_book).select_related('book')

    book_counts = {}
    for loan in user_loans:
        other_book = loan.book
        if other_book.category == current_book.category and other_book.category is not None:
            book_counts[other_book.id] = book_counts.get(other_book.id, 0) + 1

    for book_id, count in book_counts.items():
        if count >= 1:
            try:
                other_book = Book.objects.get(pk=book_id)
                weight = min(5 + count, 10)

                with transaction.atomic():
                    BookRelation.objects.get_or_create(
                        source_book=current_book,
                        target_book=other_book,
                        relation_type='also_read',
                        defaults={'weight': weight, 'is_manual': False}
                    )
                    BookRelation.objects.get_or_create(
                        source_book=other_book,
                        target_book=current_book,
                        relation_type='also_read',
                        defaults={'weight': weight, 'is_manual': False}
                    )
            except Book.DoesNotExist:
                continue
