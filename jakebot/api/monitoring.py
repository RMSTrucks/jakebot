from prometheus_client import Counter, Histogram
import time

# Define metrics
REQUESTS = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

PROCESSING_TIME = Histogram(
    'request_processing_seconds',
    'Time spent processing request',
    ['method', 'endpoint']
)

COMMITMENT_COUNT = Counter(
    'commitments_extracted_total',
    'Total number of commitments extracted'
)

ERROR_COUNT = Counter(
    'processing_errors_total',
    'Total number of processing errors',
    ['error_type']
)

TASK_CREATION = Counter(
    'tasks_created_total',
    'Total number of tasks created',
    ['system']  # 'CRM' or 'NowCerts'
)

class MetricsMiddleware:
    async def __call__(self, request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            raise
        finally:
            duration = time.time() - start_time
            REQUESTS.labels(
                method=request.method,
                endpoint=request.url.path,
                status=status_code
            ).inc()
            
            PROCESSING_TIME.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
        
        return response 