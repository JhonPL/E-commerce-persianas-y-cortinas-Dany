from django.db import DatabaseError, connection
from django.http import JsonResponse


def live(request):
    return JsonResponse({"status": "ok", "service": "notifications"})


def ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return JsonResponse(
            {"status": "not_ready", "service": "notifications"},
            status=503,
        )
    return JsonResponse({"status": "ok", "service": "notifications"})
