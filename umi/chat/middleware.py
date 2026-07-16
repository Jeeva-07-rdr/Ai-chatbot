import time
import logging

logger = logging.getLogger('umi')


class RequestLoggingMiddleware:
    """
    Middleware that logs every HTTP request with method, path, IP, user,
    response status code, and execution time in milliseconds.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        # Capture request info before processing
        method = request.method
        path = request.get_full_path()
        ip = self._get_client_ip(request)
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'

        response = self.get_response(request)

        # Calculate duration
        duration_ms = round((time.time() - start_time) * 1000, 2)
        status_code = response.status_code

        # Determine log level based on status code
        if status_code >= 500:
            logger.error(
                f"HTTP {method} {path} | Status: {status_code} | "
                f"User: {user} | IP: {ip} | Duration: {duration_ms}ms"
            )
        elif status_code >= 400:
            logger.warning(
                f"HTTP {method} {path} | Status: {status_code} | "
                f"User: {user} | IP: {ip} | Duration: {duration_ms}ms"
            )
        else:
            logger.info(
                f"HTTP {method} {path} | Status: {status_code} | "
                f"User: {user} | IP: {ip} | Duration: {duration_ms}ms"
            )

        return response

    def process_exception(self, request, exception):
        """Log unhandled exceptions with full traceback."""
        import traceback
        method = request.method
        path = request.get_full_path()
        ip = self._get_client_ip(request)
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'

        logger.critical(
            f"UNHANDLED EXCEPTION during {method} {path}\n"
            f"User: {user} | IP: {ip}\n"
            f"Exception: {type(exception).__name__}: {exception}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )
        return None  # Let Django handle the response

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
