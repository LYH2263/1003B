from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Recommendation
from apps.books.models import Category

@login_required
def recommendation_submit(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        author = request.POST.get('author', '').strip()
        publisher = request.POST.get('publisher', '').strip()
        reason = request.POST.get('reason', '').strip()
        urgency = request.POST.get('urgency', 'normal')
        
        if not title or not author:
            messages.error(request, "书名和作者不能为空。")
        elif len(reason) < 50:
            messages.error(request, "推荐理由不能少于 50 个字。")
        else:
            Recommendation.objects.create(
                user=request.user,
                title=title,
                author=author,
                publisher=publisher,
                reason=reason,
                urgency=urgency,
                status='pending'
            )
            messages.success(request, "荐书申请已提交，请等待管理员审核。")
            return redirect('my_recommendations')
    
    return render(request, 'recommendations/submit.html')

@login_required
def my_recommendations(request):
    recommendations = Recommendation.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(recommendations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'recommendations/my_list.html', {'page_obj': page_obj})

@login_required
def recommendation_manage(request):
    if request.user.role != 'admin':
        return redirect('home')
    
    status = request.GET.get('status', '')
    recommendations = Recommendation.objects.all().order_by('-created_at')
    
    if status:
        recommendations = recommendations.filter(status=status)
    
    paginator = Paginator(recommendations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'recommendations/manage.html', {'page_obj': page_obj, 'current_status': status})

@login_required
def recommendation_audit(request, pk, action):
    if request.user.role != 'admin':
        return redirect('home')
    
    recommendation = get_object_or_404(Recommendation, pk=pk)
    admin_reply = request.POST.get('admin_reply', '')
    
    if action == 'approve':
        recommendation.status = 'approved'
        recommendation.admin_reply = admin_reply
        recommendation.reviewed_at = timezone.now()
        recommendation.save()
        messages.success(request, "已采纳该荐书推荐。")
    elif action == 'reject':
        recommendation.status = 'rejected'
        recommendation.admin_reply = admin_reply
        recommendation.reviewed_at = timezone.now()
        recommendation.save()
        messages.success(request, "已拒绝该荐书推荐。")
    
    return redirect('recommendation_manage')

@login_required
def recommendation_to_book(request, pk):
    if request.user.role != 'admin':
        return redirect('home')
    
    recommendation = get_object_or_404(Recommendation, pk=pk)
    
    if recommendation.status != 'approved':
        messages.error(request, "只有已采纳的推荐才能转为入库。")
        return redirect('recommendation_manage')
    
    categories = Category.objects.all()
    return render(request, 'recommendations/to_book.html', {
        'recommendation': recommendation,
        'categories': categories
    })

def get_approved_recommendations(limit=5):
    return Recommendation.objects.filter(status='approved').order_by('-reviewed_at')[:limit]
