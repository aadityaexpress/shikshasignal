"""
Main entrypoint for ASGI runners (Uvicorn, Vercel, etc.)
"""
from src.web.app import app

__all__ = ["app"]
