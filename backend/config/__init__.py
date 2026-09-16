"""config 应用入口：导入 Celery 实例"""
from .celery import app as celery_app

__all__ = ('celery_app',)
