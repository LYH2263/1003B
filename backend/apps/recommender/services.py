from django.db.models import Count
from apps.books.models import Book, LoanRecord
from apps.users.models import User
from .models import RecommendationCache
from collections import defaultdict
import json

MIN_LOANS_FOR_RECOMMENDATION = 3
TOP_K_SIMILAR_USERS = 10
NUM_RECOMMENDATIONS = 12

def jaccard_similarity(set1, set2):
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0

def get_user_loan_books(user):
    return set(LoanRecord.objects.filter(
        user=user,
        status__in=['borrowed', 'returned']
    ).values_list('book_id', flat=True))

def get_user_based_recommendations(target_user):
    target_books = get_user_loan_books(target_user)
    
    if len(target_books) < MIN_LOANS_FOR_RECOMMENDATION:
        return get_hot_books()
    
    all_users = User.objects.filter(role='reader').exclude(pk=target_user.pk)
    user_similarities = []
    
    for user in all_users:
        user_books = get_user_loan_books(user)
        if len(user_books) > 0:
            similarity = jaccard_similarity(target_books, user_books)
            if similarity > 0:
                user_similarities.append((user, similarity, user_books))
    
    user_similarities.sort(key=lambda x: x[1], reverse=True)
    top_k_users = user_similarities[:TOP_K_SIMILAR_USERS]
    
    book_scores = defaultdict(float)
    book_common_books = defaultdict(set)
    
    for similar_user, similarity, user_books in top_k_users:
        for book_id in user_books:
            if book_id not in target_books:
                book_scores[book_id] += similarity
                common = target_books & get_user_loan_books(similar_user)
                if common:
                    book_common_books[book_id].update(list(common)[:1])
    
    sorted_books = sorted(book_scores.items(), key=lambda x: x[1], reverse=True)
    top_book_ids = [book_id for book_id, score in sorted_books[:NUM_RECOMMENDATIONS]]
    
    books = Book.objects.filter(pk__in=top_book_ids)
    book_dict = {book.pk: book for book in books}
    
    recommendations = []
    for book_id in top_book_ids:
        if book_id in book_dict:
            book = book_dict[book_id]
            common_book_ids = list(book_common_books.get(book_id, []))[:1]
            reason_book = Book.objects.filter(pk__in=common_book_ids).first() if common_book_ids else None
            
            recommendations.append({
                'id': book.pk,
                'title': book.title,
                'author': book.author,
                'cover': book.cover.url if book.cover else None,
                'category': book.category.name if book.category else None,
                'reason': f'因为你读过《{reason_book.title}》' if reason_book else '热门推荐'
            })
    
    if len(recommendations) < 6:
        hot_books = get_hot_books()
        existing_ids = {r['id'] for r in recommendations}
        for hb in hot_books:
            if hb['id'] not in existing_ids:
                recommendations.append(hb)
            if len(recommendations) >= 6:
                break
    
    return recommendations[:6]

def get_hot_books():
    hot_books = Book.objects.annotate(
        loan_count=Count('loanrecord')
    ).order_by('-loan_count')[:6]
    
    return [{
        'id': book.pk,
        'title': book.title,
        'author': book.author,
        'cover': book.cover.url if book.cover else None,
        'category': book.category.name if book.category else None,
        'reason': '热门图书',
        'is_hot': True
    } for book in hot_books]

def cache_recommendations(user):
    recommendations = get_user_based_recommendations(user)
    cache, created = RecommendationCache.objects.update_or_create(
        user=user,
        defaults={'recommendations': recommendations}
    )
    return cache

def get_cached_recommendations(user):
    try:
        cache = RecommendationCache.objects.get(user=user)
        return cache.get_recommendations()
    except RecommendationCache.DoesNotExist:
        return cache_recommendations(user).get_recommendations()

def get_recommendation_status():
    from django.db.models import Max
    total_users = User.objects.filter(role='reader').count()
    cached_users = RecommendationCache.objects.count()
    last_updated = RecommendationCache.objects.aggregate(Max('updated_at'))['updated_at__max']
    
    return {
        'total_users': total_users,
        'cached_users': cached_users,
        'coverage': (cached_users / total_users * 100) if total_users > 0 else 0,
        'last_updated': last_updated
    }
