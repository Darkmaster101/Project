from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import AppSession
import json


@csrf_exempt
@require_http_methods(["POST"])
def session_open(request):
    """Вызывается при запуске приложения."""
    data = json.loads(request.body)
    session = AppSession.objects.create(
        username=data.get("username", "unknown"),
        hostname=data.get("hostname", "unknown"),
    )
    return JsonResponse({"session_id": session.id, "opened_at": str(session.opened_at)})


@csrf_exempt
@require_http_methods(["POST"])
def session_close(request, session_id):
    """Вызывается при закрытии приложения."""
    try:
        session = AppSession.objects.get(id=session_id)
        session.closed_at = timezone.now()
        delta = session.closed_at - session.opened_at
        session.duration_seconds = int(delta.total_seconds())
        session.save()
        return JsonResponse({
            "status": "closed",
            "duration_seconds": session.duration_seconds,
        })
    except AppSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)


@require_http_methods(["GET"])
def session_list(request):
    """Последние 50 сессий."""
    sessions = AppSession.objects.all()[:50]
    data = []
    for s in sessions:
        data.append({
            "id": s.id,
            "username": s.username,
            "hostname": s.hostname,
            "opened_at": s.opened_at.strftime("%Y-%m-%d %H:%M:%S"),
            "closed_at": s.closed_at.strftime("%Y-%m-%d %H:%M:%S") if s.closed_at else None,
            "duration_seconds": s.duration_seconds,
        })
    return JsonResponse({"sessions": data})
