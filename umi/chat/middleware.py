import time
import logging
from django.shortcuts import redirect
from django.urls import reverse
from chat.repositories import AnalyticsRepository

logger = logging.getLogger('umi')


class EnterpriseAuthMiddleware:
    """
    Enterprise Authentication Middleware that protects all endpoints,
    redirects unauthenticated users to /login/?next=<path>, and sets anti-caching
    headers to prevent browser back-button access after logout.
    """
    EXEMPT_PREFIXES = (
        '/login/',
        '/register/',
        '/forgot-password/',
        '/reset-password/',
        '/static/',
        '/media/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        
        # Check if path is exempt from authentication
        is_exempt = any(path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES)
        
        if not request.user.is_authenticated and not is_exempt:
            login_url = reverse('login')
            if path != '/' and path != '':
                return redirect(f"{login_url}?next={path}")
            return redirect(login_url)

        response = self.get_response(request)

        # Enforce anti-caching headers on authenticated responses to prevent back-button caching post-logout
        if hasattr(request, 'user') and request.user.is_authenticated:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response


class RequestLoggingMiddleware:
    """
    Middleware that logs HTTP requests with method, path, IP, user,
    response status code, and execution time in milliseconds into MySQL.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        method = request.method
        path = request.get_full_path()
        ip = self._get_client_ip(request)
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'

        response = self.get_response(request)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        status_code = response.status_code

        log_msg = f"HTTP {method} {path} | Status: {status_code} | User: {user} | IP: {ip} | Duration: {duration_ms}ms"
        if status_code >= 500:
            logger.error(log_msg)
            AnalyticsRepository.log_runtime('ERROR', log_msg)
        elif status_code >= 400:
            logger.warning(log_msg)
            AnalyticsRepository.log_runtime('WARNING', log_msg)
        else:
            logger.info(log_msg)

        return response

    def process_exception(self, request, exception):
        """Log unhandled exceptions into MySQL runtime_logs table."""
        import traceback
        method = request.method
        path = request.get_full_path()
        ip = self._get_client_ip(request)
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'
        tb_str = traceback.format_exc()

        err_msg = f"UNHANDLED EXCEPTION during {method} {path} | User: {user} | IP: {ip}"
        logger.critical(f"{err_msg}\n{tb_str}")

        try:
            AnalyticsRepository.log_runtime('CRITICAL', err_msg, exception=tb_str)
        except Exception:
            pass

        return None  # Let Django handle the response

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
