"""
Alert Services Package

Provides high-level services for alert operations including:
- Alert generation
- Email notifications
- Threshold-based triggering
"""

from .alert_engine import AlertEngine

__all__ = ['AlertEngine']
