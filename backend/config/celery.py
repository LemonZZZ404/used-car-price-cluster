"""
Celery 异步任务配置
用于：模型训练异步化（网页端一键重训 + 进度查看）
"""
import os
from celery import Celery

# 设置 Django 配置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('used_car')

# 从 Django settings 读取配置（以 CELERY_ 为前缀）
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现各 app 下的 tasks.py
app.autodiscover_tasks()
