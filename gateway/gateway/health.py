from django.http import JsonResponse


def live(request):
    return JsonResponse({"status": "ok", "service": "gateway"})


def ready(request):
    return JsonResponse({"status": "ok", "service": "gateway"})
