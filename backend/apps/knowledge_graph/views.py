from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from apps.books.models import Book
from .models import BookRelation


@require_GET
def book_graph_data(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    depth = int(request.GET.get('depth', 1))

    books, relations = BookRelation.get_all_relations_for_book(book, depth=depth)

    def shorten_title(title, max_length=8):
        if len(title) <= max_length:
            return title
        return title[:max_length] + '...'

    nodes = []
    for b in books:
        nodes.append({
            'id': b.pk,
            'title': b.title,
            'short_title': shorten_title(b.title),
            'author': b.author,
            'url': f'/books/{b.pk}/',
            'is_center': b.pk == book.pk
        })

    edges = []
    seen_pairs = set()
    for rel in relations:
        pair = tuple(sorted([rel.source_book.pk, rel.target_book.pk]))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        edges.append({
            'source': rel.source_book.pk,
            'target': rel.target_book.pk,
            'type': rel.relation_type,
            'type_name': rel.get_relation_type_display(),
            'weight': rel.weight,
            'color': rel.get_color()
        })

    return JsonResponse({
        'nodes': nodes,
        'edges': edges,
        'relation_types': dict(BookRelation.RELATION_TYPE_CHOICES),
        'relation_colors': BookRelation.RELATION_COLORS
    })
