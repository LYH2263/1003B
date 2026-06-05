from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Sum
from .models import Donation, DonationBook
from apps.books.models import Book, Category
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def donation_submit(request):
    if request.method == 'POST':
        donor_name = request.POST.get('donor_name', '').strip()
        donor_phone = request.POST.get('donor_phone', '').strip()
        donor_email = request.POST.get('donor_email', '').strip()
        remark = request.POST.get('remark', '').strip()

        titles = request.POST.getlist('title[]')
        authors = request.POST.getlist('author[]')
        isbns = request.POST.getlist('isbn[]')
        quantities = request.POST.getlist('quantity[]')
        conditions = request.POST.getlist('condition[]')

        if not donor_name or not donor_phone:
            messages.error(request, '姓名和联系电话不能为空。')
            return redirect('donation_submit')

        if not any(titles):
            messages.error(request, '请至少添加一本捐赠图书。')
            return redirect('donation_submit')

        donation = Donation.objects.create(
            donor_name=donor_name,
            donor_phone=donor_phone,
            donor_email=donor_email if donor_email else None,
            remark=remark,
            status='pending'
        )

        for i in range(len(titles)):
            if titles[i].strip():
                DonationBook.objects.create(
                    donation=donation,
                    title=titles[i].strip(),
                    author=authors[i].strip() if i < len(authors) else '',
                    isbn=isbns[i].strip() if i < len(isbns) else '',
                    quantity=int(quantities[i]) if i < len(quantities) and quantities[i] else 1,
                    condition=conditions[i] if i < len(conditions) else 'good'
                )

        messages.success(request, f'捐赠申请已提交！您的追踪编号是：{donation.tracking_number}，请妥善保存。')
        return render(request, 'donations/success.html', {'tracking_number': donation.tracking_number})

    return render(request, 'donations/submit.html')


def donation_query(request):
    donation = None
    tracking_number = ''
    if request.method == 'POST':
        tracking_number = request.POST.get('tracking_number', '').strip().upper()
        if tracking_number:
            donation = Donation.objects.filter(tracking_number=tracking_number).first()
            if not donation:
                messages.error(request, '未找到该追踪编号对应的捐赠记录，请检查后重试。')

    return render(request, 'donations/query.html', {
        'donation': donation,
        'tracking_number': tracking_number
    })


@login_required
def donation_manage(request):
    if request.user.role != 'admin':
        return redirect('home')

    status = request.GET.get('status', '')
    donations = Donation.objects.all()

    if status:
        donations = donations.filter(status=status)

    paginator = Paginator(donations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    now = timezone.now()
    this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    monthly_stats = Donation.objects.filter(
        status__in=['received', 'stocked'],
        created_at__gte=this_month
    ).aggregate(
        total=Sum('books__quantity')
    )['total'] or 0

    yearly_stats = Donation.objects.filter(
        status__in=['received', 'stocked'],
        created_at__gte=this_year
    ).aggregate(
        total=Sum('books__quantity')
    )['total'] or 0

    return render(request, 'donations/manage.html', {
        'page_obj': page_obj,
        'current_status': status,
        'monthly_stats': monthly_stats,
        'yearly_stats': yearly_stats
    })


@login_required
def donation_detail(request, pk):
    if request.user.role != 'admin':
        return redirect('home')

    donation = get_object_or_404(Donation, pk=pk)
    categories = Category.objects.all()
    return render(request, 'donations/detail.html', {
        'donation': donation,
        'categories': categories
    })


@login_required
def donation_audit(request, pk, action):
    if request.user.role != 'admin':
        return redirect('home')

    donation = get_object_or_404(Donation, pk=pk)
    admin_note = request.POST.get('admin_note', '')

    if action == 'receive':
        donation.status = 'received'
        donation.reviewed_by = request.user
        donation.reviewed_at = timezone.now()
        donation.admin_note = admin_note
        donation.save()
        messages.success(request, '已确认接收该捐赠。')
    elif action == 'reject':
        donation.status = 'rejected'
        donation.reviewed_by = request.user
        donation.reviewed_at = timezone.now()
        donation.admin_note = admin_note
        donation.save()
        messages.success(request, '已拒绝该捐赠申请。')

    return redirect('donation_detail', pk=pk)


@login_required
def donation_to_books(request, pk):
    if request.user.role != 'admin':
        return redirect('home')

    donation = get_object_or_404(Donation, pk=pk)

    if donation.status != 'received':
        messages.error(request, '只有已接收状态的捐赠才能入库。')
        return redirect('donation_detail', pk=pk)

    if request.method == 'POST':
        book_ids = request.POST.getlist('book_ids[]')
        category_ids = request.POST.getlist('category_id[]')
        descriptions = request.POST.getlist('description[]')

        success_count = 0
        for i, book_id in enumerate(book_ids):
            try:
                donation_book = DonationBook.objects.get(id=book_id, donation=donation)
                if not donation_book.added_to_library:
                    category_id = category_ids[i] if i < len(category_ids) else None
                    description = descriptions[i] if i < len(descriptions) else ''

                    category = Category.objects.get(id=category_id) if category_id else None

                    existing_book = Book.objects.filter(isbn=donation_book.isbn).first() if donation_book.isbn else None
                    if existing_book:
                        existing_book.stock += donation_book.quantity
                        existing_book.total_stock += donation_book.quantity
                        existing_book.save()
                    else:
                        Book.objects.create(
                            title=donation_book.title,
                            author=donation_book.author,
                            isbn=donation_book.isbn,
                            category=category,
                            description=description,
                            stock=donation_book.quantity,
                            total_stock=donation_book.quantity
                        )

                    donation_book.added_to_library = True
                    donation_book.save()
                    success_count += 1
            except Exception as e:
                continue

        if all(book.added_to_library for book in donation.books.all()):
            donation.status = 'stocked'
            donation.save()

        messages.success(request, f'成功入库 {success_count} 种图书。')
        return redirect('donation_detail', pk=pk)

    return redirect('donation_detail', pk=pk)


@login_required
def generate_thank_you_pdf(request, pk):
    if request.user.role != 'admin':
        return redirect('home')

    donation = get_object_or_404(Donation, pk=pk)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="感谢信_{donation.tracking_number}.pdf"'

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.darkblue,
        alignment=1,
        spaceAfter=30
    )
    normal_style = styles['Normal']
    normal_style.fontSize = 12
    normal_style.leading = 20

    elements = []

    elements.append(Paragraph('感 谢 信', title_style))
    elements.append(Spacer(1, 1 * cm))

    elements.append(Paragraph(f'尊敬的 {donation.donor_name} 先生/女士：', normal_style))
    elements.append(Spacer(1, 0.5 * cm))

    letter_content = f'''
    <br/>
    &nbsp;&nbsp;&nbsp;&nbsp;感谢您向我馆捐赠图书，您的爱心善举将帮助更多读者获取知识，丰富我馆的馆藏资源。
    <br/><br/>
    &nbsp;&nbsp;&nbsp;&nbsp;您本次捐赠的图书清单如下：
    <br/><br/>
    '''
    elements.append(Paragraph(letter_content, normal_style))

    table_data = [['序号', '书名', '作者', 'ISBN', '数量', '新旧程度']]
    for i, book in enumerate(donation.books.all(), 1):
        table_data.append([
            str(i),
            book.title,
            book.author,
            book.isbn or '-',
            str(book.quantity),
            book.get_condition_display_cn()
        ])

    table = Table(table_data, colWidths=[1 * cm, 4 * cm, 3 * cm, 3 * cm, 1.5 * cm, 2.5 * cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    elements.append(table)

    elements.append(Spacer(1, 1 * cm))

    closing = f'''
    <br/>
    &nbsp;&nbsp;&nbsp;&nbsp;再次感谢您的慷慨捐赠！我们将妥善保管这些图书，让它们发挥最大的价值。
    <br/><br/><br/>
    <div align="right">龙猫图书借阅管理系统</div>
    <div align="right">{donation.created_at.strftime("%Y年%m月%d日")}</div>
    '''
    elements.append(Paragraph(closing, normal_style))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response
