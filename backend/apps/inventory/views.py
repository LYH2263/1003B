from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from .models import StockAlert
import csv


@login_required
def stock_alert_list(request):
    if request.user.role != 'admin':
        return redirect('home')

    status_filter = request.GET.get('status', 'pending')
    type_filter = request.GET.get('type', '')

    alerts = StockAlert.objects.select_related('book').all()

    if status_filter:
        alerts = alerts.filter(status=status_filter)
    if type_filter:
        alerts = alerts.filter(alert_type=type_filter)

    alerts = alerts.order_by('-created_at')

    paginator = Paginator(alerts, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    stats = {
        'pending': StockAlert.objects.filter(status='pending').count(),
        'resolved': StockAlert.objects.filter(status='resolved').count(),
        'ignored': StockAlert.objects.filter(status='ignored').count(),
        'total': StockAlert.objects.count(),
    }

    return render(request, 'admin/stock_alerts.html', {
        'alerts': page_obj,
        'stats': stats,
        'status_filter': status_filter,
        'type_filter': type_filter,
    })


@login_required
def stock_alert_mark_resolved(request, pk):
    if request.user.role != 'admin':
        return redirect('home')

    alert = get_object_or_404(StockAlert, pk=pk)
    alert.status = 'resolved'
    alert.save()
    messages.success(request, f"预警《{alert.book.title}》已标记为已处理。")
    return redirect('stock_alert_list')


@login_required
def stock_alert_mark_ignored(request, pk):
    if request.user.role != 'admin':
        return redirect('home')

    alert = get_object_or_404(StockAlert, pk=pk)
    alert.status = 'ignored'
    alert.save()
    messages.success(request, f"预警《{alert.book.title}》已忽略。")
    return redirect('stock_alert_list')


@login_required
def export_purchase_suggestions_csv(request):
    if request.user.role != 'admin':
        return redirect('home')

    alerts = StockAlert.objects.filter(
        status='pending',
        alert_type__in=['low_stock', 'high_demand'],
        suggested_purchase_qty__gt=0
    ).select_related('book').order_by('-suggested_purchase_qty')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="purchase_suggestions.csv"'

    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['书名', 'ISBN', '作者', '预警类型', '当前库存', '建议采购数量'])

    for alert in alerts:
        writer.writerow([
            alert.book.title,
            alert.book.isbn or '',
            alert.book.author,
            alert.get_alert_type_display(),
            alert.book.stock,
            alert.suggested_purchase_qty,
        ])

    return response
