try:
    from .celery import app as celery_app
except ImportError:
    # Celery not installed, continue without it
    pass

__all__ = ("celery_app",)
