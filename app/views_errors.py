from django.http import JsonResponse
from django.shortcuts import render

def handler404(request, exception=None):
    return render(request, '404.html', status=404)

def handler500(request):
    return render(request, '500.html', status=500)


def health_check(request):
    """Simple health check endpoint — no auth, no DB, always 200."""
    return JsonResponse({'status': 'ok'})
