from .services import get_unresolved_count


def stock_alert_badge(request):
    if request.user.is_authenticated and request.user.role == 'admin':
        return {
            'unresolved_stock_alerts': get_unresolved_count()
        }
    return {}
