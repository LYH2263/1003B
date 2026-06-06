from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from apps.books.models import Book, LoanRecord
from .models import StockAlert


class StockAlertConfig:
    LOW_STOCK_RATIO = 0.2
    LOW_STOCK_LOAN_DAYS = 30
    SLOW_MOVING_DAYS = 90
    SLOW_MOVING_MIN_STOCK = 3
    HIGH_DEMAND_DAYS = 30
    HIGH_DEMAND_MULTIPLIER = 2


def get_loan_count_in_days(book, days):
    threshold = timezone.now().date() - timedelta(days=days)
    return LoanRecord.objects.filter(
        book=book,
        borrow_date__gte=threshold
    ).count()


def check_low_stock(book):
    if book.total_stock == 0:
        return False, None
    stock_ratio = book.stock / book.total_stock
    loan_count_30 = get_loan_count_in_days(book, StockAlertConfig.LOW_STOCK_LOAN_DAYS)
    if stock_ratio <= StockAlertConfig.LOW_STOCK_RATIO and loan_count_30 > 0:
        suggested_qty = max(loan_count_30 - book.stock, 1)
        description = (
            f"当前库存 {book.stock} 本，占总库存 {book.total_stock} 本的 "
            f"{stock_ratio*100:.1f}%，近30天借阅 {loan_count_30} 次，库存不足。"
        )
        suggested_action = f"建议采购 {suggested_qty} 本以满足借阅需求。"
        return True, {
            'description': description,
            'suggested_action': suggested_action,
            'suggested_purchase_qty': suggested_qty
        }
    return False, None


def check_slow_moving(book):
    loan_count_90 = get_loan_count_in_days(book, StockAlertConfig.SLOW_MOVING_DAYS)
    if loan_count_90 == 0 and book.stock > StockAlertConfig.SLOW_MOVING_MIN_STOCK:
        description = (
            f"近 {StockAlertConfig.SLOW_MOVING_DAYS} 天无借阅记录，当前库存 {book.stock} 本，"
            f"库存积压严重，属于长期滞销图书。"
        )
        suggested_action = "建议开展促销活动、调整馆藏位置或考虑下架处理。"
        return True, {
            'description': description,
            'suggested_action': suggested_action,
            'suggested_purchase_qty': 0
        }
    return False, None


def check_high_demand(book):
    if book.total_stock == 0:
        return False, None
    loan_count_30 = get_loan_count_in_days(book, StockAlertConfig.HIGH_DEMAND_DAYS)
    threshold = book.total_stock * StockAlertConfig.HIGH_DEMAND_MULTIPLIER
    if loan_count_30 >= threshold and threshold > 0:
        suggested_qty = max(loan_count_30 - book.stock, 1)
        description = (
            f"近 {StockAlertConfig.HIGH_DEMAND_DAYS} 天借阅 {loan_count_30} 次，"
            f"总库存 {book.total_stock} 本，借阅量是库存的 "
            f"{loan_count_30/book.total_stock:.1f} 倍，供不应求。"
        )
        suggested_action = f"建议采购 {suggested_qty} 本以缓解供需矛盾。"
        return True, {
            'description': description,
            'suggested_action': suggested_action,
            'suggested_purchase_qty': suggested_qty
        }
    return False, None


ALERT_CHECKS = [
    ('low_stock', check_low_stock),
    ('slow_moving', check_slow_moving),
    ('high_demand', check_high_demand),
]


def scan_and_generate_alerts():
    books = Book.objects.all()
    new_alerts = []
    skipped = 0

    for book in books:
        for alert_type, check_func in ALERT_CHECKS:
            triggered, data = check_func(book)
            if triggered:
                existing = StockAlert.objects.filter(
                    book=book,
                    alert_type=alert_type,
                    status='pending'
                ).exists()
                if not existing:
                    alert = StockAlert(
                        book=book,
                        alert_type=alert_type,
                        description=data['description'],
                        suggested_action=data['suggested_action'],
                        suggested_purchase_qty=data['suggested_purchase_qty'],
                        status='pending'
                    )
                    new_alerts.append(alert)
                else:
                    skipped += 1

    if new_alerts:
        StockAlert.objects.bulk_create(new_alerts)

    return {
        'total_books': books.count(),
        'new_alerts': len(new_alerts),
        'skipped': skipped
    }


def get_unresolved_count():
    return StockAlert.objects.filter(status='pending').count()
