"""
API PACKAGE
Exports main FastAPI application.
"""

from .main import app, create_app
from .dependencies import get_settings

__all__ = [
    "app",
    "create_app",
    "get_settings",
]
