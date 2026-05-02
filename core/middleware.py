"""
Custom middleware for DeepTrade:
 - HealthCheckMiddleware : keeps GET /health/ alive without DB/auth (used by Render/Heroku)
 - APIErrorMiddleware    : catches unhandled exceptions from yfinance/groq and shows a
                           friendly 500 page instead of a raw crash trace.
"""
import logging
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)


class HealthCheckMiddleware:
    """Responds to /health/ immediately — no DB, no auth required."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/health/':
            return JsonResponse({'status': 'ok'}, status=200)
        return self.get_response(request)


class APIErrorMiddleware:
    """
    Catches any unhandled exception that escapes a view and renders a friendly
    error page instead of Django's default 500 (or a blank crash).
    Only active when DEBUG=False — in dev mode Django's debug page is more useful.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        from django.conf import settings as dj_settings
        if dj_settings.DEBUG:
            return None   # let Django's debug page handle it
        logger.error(f'Unhandled exception on {request.path}: {exception}', exc_info=True)
        try:
            return render(request, '500.html', status=500)
        except Exception:
            return HttpResponse(
                '<h1>Something went wrong</h1><p>Please try again later.</p>',
                status=500,
                content_type='text/html',
            )
