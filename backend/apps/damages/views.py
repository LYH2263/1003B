from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date
from .models import DamageReport, DamageImage
from apps.books.models import LoanRecord, Book
from apps.notifications.services import send_notification


@login_required
def damage_manage(request):
    if request.user.role != 'admin':
        return redirect('home')

    damages_list = DamageReport.objects.all().order_by('-created_at')

    status = request.GET.get('status')
    level = request.GET.get('level')
    user_query = request.GET.get('user')

    if status:
        damages_list = damages_list.filter(status=status)
    if level:
        damages_list = damages_list.filter(damage_level=level)
    if user_query:
        damages_list = damages_list.filter(user__username__icontains=user_query)

    paginator = Paginator(damages_list, 10)
    page_number = request.GET.get('page')
    damages = paginator.get_page(page_number)

    today = timezone.now().date()
    month_start = today.replace(day=1)
    monthly_stats = {
        'monthly_count': DamageReport.objects.filter(created_at__date__gte=month_start).count(),
        'total_compensation': DamageReport.objects.filter(
            status='compensated'
        ).aggregate(total=Sum('compensation_amount'))['total'] or 0,
        'pending_count': DamageReport.objects.filter(status='pending_assessment').count(),
        'pending_compensation': DamageReport.objects.filter(status='pending_compensation').count(),
    }

    return render(request, 'admin/damage_list.html', {
        'damages': damages,
        'monthly_stats': monthly_stats,
    })


@login_required
def damage_report_create(request, loan_id):
    if request.user.role != 'admin':
        return redirect('home')

    loan = get_object_or_404(LoanRecord, pk=loan_id)

    if loan.status != 'borrowed':
        messages.error(request, '该借阅记录状态不允许创建损坏报告。')
        return redirect('loan_manage')

    if hasattr(loan, 'damage_report'):
        messages.warning(request, '该借阅记录已有损坏报告。')
        return redirect('damages:damage_detail', pk=loan.damage_report.id)

    if request.method == 'POST':
        damage_level = request.POST.get('damage_level')
        description = request.POST.get('description', '')
        images = request.FILES.getlist('images')

        if not damage_level:
            messages.error(request, '请选择损坏等级。')
            return redirect('damages:damage_report_create', loan_id=loan_id)

        if len(images) < 1 or len(images) > 5:
            messages.error(request, '请上传 1-5 张证据图片。')
            return redirect('damages:damage_report_create', loan_id=loan_id)

        damage_report = DamageReport.objects.create(
            loan=loan,
            book=loan.book,
            user=loan.user,
            damage_level=damage_level,
            description=description,
            status='pending_assessment'
        )

        for img in images:
            DamageImage.objects.create(
                damage_report=damage_report,
                image=img
            )

        loan.status = 'damaged'
        loan.return_date = date.today()
        loan.save()

        send_notification(
            recipient=loan.user,
            notification_type='damage_report',
            title='图书损坏通知',
            content=f'您借阅的《{loan.book.title}》归还时发现损坏，请及时查看并处理赔偿事宜。',
            related_object_id=damage_report.id
        )

        messages.success(request, '损坏报告已创建，借阅状态已更新为待赔偿。')
        return redirect('damages:damage_detail', pk=damage_report.id)

    return render(request, 'admin/damage_report_form.html', {'loan': loan})


@login_required
def damage_detail(request, pk):
    damage = get_object_or_404(DamageReport, pk=pk)

    if request.user.role != 'admin' and request.user.id != damage.user_id:
        return redirect('home')

    return render(request, 'damages/detail.html', {'damage': damage})


@login_required
def damage_assess(request, pk):
    if request.user.role != 'admin':
        return redirect('home')

    damage = get_object_or_404(DamageReport, pk=pk)

    if damage.status != 'pending_assessment':
        messages.error(request, '该报告状态不允许评估。')
        return redirect('damages:damage_detail', pk=pk)

    if request.method == 'POST':
        amount = request.POST.get('compensation_amount')

        try:
            amount = float(amount)
            if amount < 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, '请输入有效的赔偿金额。')
            return redirect('damages:damage_detail', pk=pk)

        damage.compensation_amount = amount
        damage.status = 'pending_compensation'
        damage.assessed_by = request.user
        damage.assessed_at = timezone.now()
        damage.save()

        send_notification(
            recipient=damage.user,
            notification_type='damage_assessment',
            title='损坏评估结果',
            content=f'您的《{damage.book.title}》损坏报告已评估，赔偿金额为 ¥{amount}，请及时处理。',
            related_object_id=damage.id
        )

        messages.success(request, '评估完成，已通知读者。')
        return redirect('damages:damage_detail', pk=pk)

    return redirect('damages:damage_detail', pk=pk)


@login_required
def damage_compensate(request, pk):
    if request.user.role != 'admin':
        return redirect('home')

    damage = get_object_or_404(DamageReport, pk=pk)

    if damage.status != 'pending_compensation':
        messages.error(request, '该报告状态不允许确认赔偿。')
        return redirect('damages:damage_detail', pk=pk)

    if request.method == 'POST':
        damage.status = 'compensated'
        damage.processed_at = timezone.now()
        damage.save()

        if damage.damage_level in ['minor', 'moderate']:
            damage.book.stock += 1
            damage.book.save()
        elif damage.damage_level in ['severe', 'lost']:
            damage.book.total_stock -= 1
            if damage.book.total_stock < 0:
                damage.book.total_stock = 0
            damage.book.save()

        damage.loan.status = 'returned'
        damage.loan.save()

        send_notification(
            recipient=damage.user,
            notification_type='damage_completed',
            title='赔偿已确认',
            content=f'您的《{damage.book.title}》损坏赔偿已确认，感谢您的配合。',
            related_object_id=damage.id
        )

        messages.success(request, '赔偿已确认，图书库存已根据损坏等级处理。')
        return redirect('damages:damage_detail', pk=pk)

    return redirect('damages:damage_detail', pk=pk)


@login_required
def damage_waive(request, pk):
    if request.user.role != 'admin':
        return redirect('home')

    damage = get_object_or_404(DamageReport, pk=pk)

    if damage.status not in ['pending_assessment', 'pending_compensation']:
        messages.error(request, '该报告状态不允许免除。')
        return redirect('damages:damage_detail', pk=pk)

    if request.method == 'POST':
        damage.status = 'waived'
        damage.processed_at = timezone.now()
        damage.assessed_by = request.user
        if not damage.assessed_at:
            damage.assessed_at = timezone.now()
        damage.save()

        if damage.damage_level in ['minor', 'moderate']:
            damage.book.stock += 1
            damage.book.save()
        elif damage.damage_level in ['severe', 'lost']:
            damage.book.total_stock -= 1
            if damage.book.total_stock < 0:
                damage.book.total_stock = 0
            damage.book.save()

        damage.loan.status = 'returned'
        damage.loan.save()

        send_notification(
            recipient=damage.user,
            notification_type='damage_waived',
            title='赔偿已免除',
            content=f'您的《{damage.book.title}》损坏赔偿已被免除。',
            related_object_id=damage.id
        )

        messages.success(request, '已免除赔偿，图书库存已根据损坏等级处理。')
        return redirect('damages:damage_detail', pk=pk)

    return redirect('damages:damage_detail', pk=pk)
